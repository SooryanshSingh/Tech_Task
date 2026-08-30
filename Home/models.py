


from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import now



class StudentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    profile_image = models.ImageField(
        upload_to="student_profiles/"
    )
    embedding = models.JSONField(
    null=True,
    blank=True
)
    
class Exam(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exams')
    examinees = models.ManyToManyField(User, related_name='assigned_exams', blank=True)
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=False, blank=False)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    attempted = models.BooleanField(default=False)  
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(end_time__gt=models.F("start_time")),
                name="exam_end_after_start",
            ),
            models.CheckConstraint(
                condition=Q(duration__gt=0),
                name="exam_duration_positive",
            ),
        ]


    def __str__(self):
        return self.title

    @property
    def questions_are_locked(self):
        return bool(
            self.closed_at
            or self.start_time <= timezone.now()
            or self.attempts.exclude(status=ExamAttempt.Status.NOT_STARTED).exists()
        )

    def assert_questions_editable(self):
        if self.questions_are_locked:
            raise ValidationError(
                "Questions cannot be changed after the exam has started."
            )


class ExamAttempt(models.Model):
    class Status(models.TextChoices):
        NOT_STARTED = "NOT_STARTED", "Not started"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        SUBMITTED = "SUBMITTED", "Submitted"
        TERMINATED = "TERMINATED", "Terminated"

    exam = models.ForeignKey(
        Exam, on_delete=models.CASCADE, related_name="attempts"
    )
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="exam_attempts"
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NOT_STARTED
    )
    started_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("exam", "student"), name="unique_exam_attempt_per_student"
            )
        ]

    def __str__(self):
        return f"{self.exam} - {self.student} ({self.status})"

class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("question",),
                condition=Q(is_correct=True),
                name="unique_correct_answer_per_question",
            )
        ]
class Feedback(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])

class Response(models.Model):
    attempt = models.ForeignKey(
        ExamAttempt,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="responses",
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='responses')
    text = models.TextField()

    def __str__(self):
        return f"Response for question: {self.question.text} by {self.student.username}"
class ProctorEmail(models.Model):
    email = models.EmailField(unique=True)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proctor_emails')

    def __str__(self):
        return self.email




class Timer(models.Model):
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name="timer")
    start_time = models.DateTimeField(null=True, blank=True)

    def start_timer(self):
        if not self.start_time:
            self.start_time = now()
            self.save()

    def get_remaining_time(self):
        if not self.start_time:
            return self.exam.duration * 60  

        elapsed_time = (now() - self.start_time).total_seconds()
        return max(0, self.exam.duration * 60 - elapsed_time)


import uuid

class ExamInvite(models.Model):

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE
    )

    email = models.EmailField()

    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )

    used = models.BooleanField(
        default=False
    )

    accepted_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
