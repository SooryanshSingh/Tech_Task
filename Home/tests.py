from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Answer, Exam, ExamAttempt, Question
from .services.question_service import save_question_with_answers


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class SignupRoleTests(TestCase):
    def test_test_admin_label_stores_company_value_and_assigns_company_group(self):
        response = self.client.post(reverse("signup"), {
            "username": "test-admin",
            "email": "admin@example.com",
            "password1": "A-strong-password-123!",
            "password2": "A-strong-password-123!",
            "role": "Company",
        })

        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username="test-admin")
        self.assertFalse(user.is_active)
        self.assertTrue(user.groups.filter(name="Company").exists())


class QuestionIntegrityTests(TestCase):
    def setUp(self):
        self.company = User.objects.create_user("company", password="pw")
        self.exam = Exam.objects.create(
            title="Future exam",
            description="Test",
            company=self.company,
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=1),
            duration=30,
        )
        self.question_data = {
            "text": "2 + 2?",
            "option_a": "1",
            "option_b": "2",
            "option_c": "3",
            "option_d": "4",
            "correct_option": "D",
        }

    def test_service_creates_exactly_four_answers_and_one_correct_answer(self):
        question = save_question_with_answers(
            exam=self.exam,
            cleaned_data=self.question_data,
        )

        self.assertEqual(question.answers.count(), 4)
        self.assertEqual(question.answers.filter(is_correct=True).count(), 1)
        self.assertEqual(question.answers.get(is_correct=True).text, "4")

    def test_database_rejects_a_second_correct_answer(self):
        question = Question.objects.create(exam=self.exam, text="Question")
        Answer.objects.create(question=question, text="A", is_correct=True)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Answer.objects.create(question=question, text="B", is_correct=True)

    def test_questions_are_frozen_after_exam_starts(self):
        self.exam.start_time = timezone.now() - timedelta(seconds=1)
        self.exam.save(update_fields=["start_time"])

        with self.assertRaisesMessage(
            ValidationError,
            "Questions cannot be changed after the exam has started.",
        ):
            save_question_with_answers(
                exam=self.exam,
                cleaned_data=self.question_data,
            )


class AttemptScoreTests(TestCase):
    def test_marks_page_uses_attempt_score(self):
        company = User.objects.create_user("score-company", password="pw")
        Group.objects.get_or_create(name="Company")[0].user_set.add(company)
        student = User.objects.create_user("score-student", password="pw")
        exam = Exam.objects.create(
            title="Scored exam",
            description="Test",
            company=company,
            start_time=timezone.now() - timedelta(hours=1),
            end_time=timezone.now() + timedelta(hours=1),
            duration=30,
        )
        ExamAttempt.objects.create(
            exam=exam,
            student=student,
            status=ExamAttempt.Status.SUBMITTED,
            score=7,
        )
        self.client.force_login(company)

        response = self.client.get(reverse("marks"))

        self.assertContains(response, "Marks: 7")
        self.assertContains(response, "score-student")
