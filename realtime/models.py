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
