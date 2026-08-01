from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("Home", "0024_examinvite"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExamAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("NOT_STARTED", "Not started"), ("IN_PROGRESS", "In progress"), ("SUBMITTED", "Submitted"), ("TERMINATED", "Terminated")], default="NOT_STARTED", max_length=20)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("score", models.PositiveIntegerField(blank=True, null=True)),
                ("exam", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attempts", to="Home.exam")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exam_attempts", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name="examattempt",
            constraint=models.UniqueConstraint(fields=("exam", "student"), name="unique_exam_attempt_per_student"),
        ),
        migrations.AddField(
            model_name="response",
            name="attempt",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="responses", to="Home.examattempt"),
        ),
        migrations.AddField(
            model_name="mark",
            name="attempt",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="mark", to="Home.examattempt"),
        ),
    ]
