from django.db import models
from django.contrib.auth.models import User
from Home.models import Exam


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