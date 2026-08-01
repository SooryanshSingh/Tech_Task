from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from Home.models import Answer, Exam, ExamAttempt, Question


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
