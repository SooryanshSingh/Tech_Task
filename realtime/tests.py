import base64
from datetime import timedelta
from unittest.mock import patch

from asgiref.sync import async_to_sync
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from Home.models import Answer, Exam, ExamAttempt, Question
from exam.routing import websocket_urlpatterns
from realtime.consumer import MAX_EVIDENCE_PER_SESSION, TabMonitorConsumer
from realtime.models import ExamAuditLog, ExamReport, ExamSession
from realtime.reporting import build_report_bytes
from realtime.tasks import generate_exam_report


class ExamAttemptTests(TestCase):
    def setUp(self):
        self.company = User.objects.create_user("company", password="pw")
        self.student_a = User.objects.create_user("student-a", password="pw")
        self.student_b = User.objects.create_user("student-b", password="pw")
        student_group, _ = Group.objects.get_or_create(name="Student")
        self.student_a.groups.add(student_group)
        self.student_b.groups.add(student_group)
        self.exam = Exam.objects.create(
            title="SDE Test",
            description="Test",
            company=self.company,
            start_time=timezone.now() - timedelta(minutes=5),
            end_time=timezone.now() + timedelta(hours=1),
            duration=30,
        )
        self.exam.examinees.add(self.student_a, self.student_b)
        self.question = Question.objects.create(exam=self.exam, text="2 + 2?")
        self.answer = Answer.objects.create(
            question=self.question, text="4", is_correct=True
        )

    def test_each_student_gets_an_independent_timer(self):
        for student in (self.student_a, self.student_b):
            self.client.force_login(student)
            response = self.client.get(
                reverse("get_remaining_time", args=[self.exam.pk])
            )
            self.assertEqual(response.status_code, 200)

        attempts = ExamAttempt.objects.filter(exam=self.exam).order_by("student_id")
        self.assertEqual(attempts.count(), 2)
        self.assertTrue(all(attempt.started_at for attempt in attempts))

    def test_unassigned_student_cannot_open_exam(self):
        outsider = User.objects.create_user("outsider", password="pw")
        outsider.groups.add(Group.objects.get(name="Student"))
        self.client.force_login(outsider)
        response = self.client.get(reverse("test_with_chat", args=[self.exam.pk]))
        self.assertEqual(response.status_code, 403)

    def test_submission_is_per_student_and_idempotent(self):
        self.client.force_login(self.student_a)
        url = reverse("test_with_chat", args=[self.exam.pk])
        response = self.client.post(
            url, {f"answer_{self.question.pk}": str(self.answer.pk)}
        )
        self.assertEqual(response.status_code, 302)

        attempt = ExamAttempt.objects.get(exam=self.exam, student=self.student_a)
        self.assertEqual(attempt.status, ExamAttempt.Status.SUBMITTED)
        self.assertEqual(attempt.score, 1)
        self.assertFalse(
            ExamAttempt.objects.filter(exam=self.exam, student=self.student_b).exists()
        )

        second_response = self.client.post(
            url, {f"answer_{self.question.pk}": str(self.answer.pk)}
        )
        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(attempt.responses.count(), 1)

    def test_answer_from_another_question_is_rejected(self):
        other_question = Question.objects.create(exam=self.exam, text="Other")
        other_answer = Answer.objects.create(
            question=other_question, text="wrong scope", is_correct=True
        )
        self.client.force_login(self.student_a)
        response = self.client.post(
            reverse("test_with_chat", args=[self.exam.pk]),
            {f"answer_{self.question.pk}": str(other_answer.pk)},
        )
        self.assertEqual(response.status_code, 400)


class PhoneDetectionSecurityTests(TestCase):
    def test_anonymous_request_is_redirected(self):
        response = Client().post(reverse("detect_phone"), {"image": "data"})
        self.assertEqual(response.status_code, 302)

    def test_csrf_is_required(self):
        student = User.objects.create_user("student", password="pw")
        group, _ = Group.objects.get_or_create(name="Student")
        student.groups.add(group)
        client = Client(enforce_csrf_checks=True)
        client.force_login(student)
        response = client.post(reverse("detect_phone"), {"image": "data"})
        self.assertEqual(response.status_code, 403)


class ProctorCloseTests(TestCase):
    def setUp(self):
        self.company = User.objects.create_user("close-company", password="pw")
        self.student = User.objects.create_user("close-student", password="pw")
        student_group, _ = Group.objects.get_or_create(name="Student")
        self.student.groups.add(student_group)
        self.exam = Exam.objects.create(
            title="Close test",
            description="Test",
            company=self.company,
            start_time=timezone.now() - timedelta(minutes=5),
            end_time=timezone.now() + timedelta(hours=1),
            duration=30,
        )
        self.exam.examinees.add(self.student)
        self.attempt = ExamAttempt.objects.create(
            exam=self.exam,
            student=self.student,
            status=ExamAttempt.Status.IN_PROGRESS,
            started_at=timezone.now(),
        )

    def test_proctor_close_persists_exam_and_attempt_termination(self):
        async def close_over_websocket():
            communicator = WebsocketCommunicator(
                URLRouter(websocket_urlpatterns),
                f"/ws/exam/{self.exam.pk}/",
            )
            communicator.scope["user"] = self.company
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            await communicator.send_json_to({"type": "close_exam"})
            event = await communicator.receive_json_from()
            await communicator.disconnect()
            return event

        event = async_to_sync(close_over_websocket)()

        self.assertEqual(event["type"], "exam_closed")
        self.assertEqual(event["terminated_attempts"], 1)
        self.exam.refresh_from_db()
        self.attempt.refresh_from_db()
        self.assertIsNotNone(self.exam.closed_at)
        self.assertEqual(self.attempt.status, ExamAttempt.Status.TERMINATED)
        self.assertIsNotNone(self.attempt.submitted_at)

    def test_closed_exam_cannot_create_a_fresh_attempt(self):
        self.attempt.delete()
        self.exam.closed_at = timezone.now()
        self.exam.save(update_fields=["closed_at"])
        self.client.force_login(self.student)

        response = self.client.get(reverse("test_with_chat", args=[self.exam.pk]))

        self.assertRedirects(response, reverse("test_end", args=[self.exam.pk]))
        self.assertFalse(
            ExamAttempt.objects.filter(exam=self.exam, student=self.student).exists()
        )


class EvidenceQuotaTests(TestCase):
    def test_evidence_quota_is_checked_while_session_row_is_locked(self):
        company = User.objects.create_user("evidence-company", password="pw")
        student = User.objects.create_user("evidence-student", password="pw")
        exam = Exam.objects.create(
            title="Evidence exam",
            description="Test",
            company=company,
            start_time=timezone.now() - timedelta(minutes=5),
            end_time=timezone.now() + timedelta(hours=1),
            duration=30,
        )
        session = ExamSession.objects.create(
            exam=exam,
            user=student,
            session_id=f"{exam.pk}_user_{student.pk}",
            evidence_count=MAX_EVIDENCE_PER_SESSION,
        )
        consumer = TabMonitorConsumer()
        consumer.exam_id = exam.pk
        consumer.user = student
        consumer.session_id = session.session_id
        evidence = "data:image/jpeg;base64," + base64.b64encode(b"image").decode()

        updated_session, log = async_to_sync(consumer.record_violation)(
            session,
            "NO_FACE",
            20,
            evidence,
        )

        self.assertEqual(updated_session.evidence_count, MAX_EVIDENCE_PER_SESSION)
        self.assertFalse(bool(log.evidence_image))
        self.assertEqual(updated_session.violation_count, 1)


class AsyncReportTests(TestCase):
    def setUp(self):
        self.company = User.objects.create_user("report-company", password="pw")
        self.student = User.objects.create_user("report-student", password="pw")
        self.exam = Exam.objects.create(
            title="Report exam",
            description="Test",
            company=self.company,
            start_time=timezone.now() - timedelta(minutes=5),
            end_time=timezone.now() + timedelta(hours=1),
            duration=30,
        )
        self.session = ExamSession.objects.create(
            exam=self.exam,
            user=self.student,
            session_id=f"{self.exam.pk}_user_{self.student.pk}",
        )
        ExamAuditLog.objects.create(
            exam=self.exam,
            actor=self.student,
            session_id=self.session.session_id,
            event_type="NO_FACE",
            severity=20,
            evidence_image=SimpleUploadedFile(
                "evidence.png",
                base64.b64decode(
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
                ),
                content_type="image/png",
            ),
        )

    def test_report_builder_uses_storage_open_and_produces_pdf(self):
        pdf_bytes = build_report_bytes(self.exam)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_report_task_saves_generated_pdf_through_storage(self):
        report = ExamReport.objects.create(
            exam=self.exam,
            requested_by=self.company,
        )

        generate_exam_report.run(report.pk)

        report.refresh_from_db()
        self.assertEqual(report.status, ExamReport.Status.READY)
        self.assertTrue(bool(report.file))
        with report.file.open("rb") as report_file:
            self.assertTrue(report_file.read(4).startswith(b"%PDF"))

    @patch("realtime.views.generate_exam_report.delay")
    def test_report_request_queues_task_after_commit(self, delay):
        self.client.force_login(self.company)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.get(
                reverse("generate_report", args=[self.exam.pk])
            )

        report = ExamReport.objects.get(exam=self.exam)
        self.assertRedirects(response, reverse("report_status", args=[report.pk]))
        delay.assert_called_once_with(report.pk)
