from django.db import models
from django.contrib.auth.models import User
from Home.models import Exam

class ExamSession(models.Model):

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    session_id = models.CharField(
        max_length=120,
        unique=True
    )

    violation_count = models.IntegerField(
        default=0
    )

    risk_score = models.IntegerField(
        default=0
    )

    evidence_count = models.PositiveIntegerField(
        default=0
    )

    latest_event = models.CharField(
        max_length=50,
        default="CONNECTED"
    )

    is_active = models.BooleanField(
        default=True
    )
    class Meta:
        unique_together = (
            "exam",
            "user"
        )



class ExamAuditLog(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)

    actor = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL
    )

    session_id = models.CharField(
        max_length=120,
        null=True,
        blank=True
    )

    event_type = models.CharField(max_length=50)

    severity = models.IntegerField(default=0)

    metadata = models.JSONField(default=dict, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    evidence_image = models.ImageField(
        upload_to="audit_evidence/",
        null=True,
        blank=True
    )


class ExamReport(models.Model):
    class Status(models.TextChoices):
        QUEUED = "QUEUED", "Queued"
        PROCESSING = "PROCESSING", "Processing"
        READY = "READY", "Ready"
        FAILED = "FAILED", "Failed"

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="reports")
    requested_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="requested_exam_reports",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.QUEUED,
    )
    file = models.FileField(upload_to="exam_reports/", null=True, blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
