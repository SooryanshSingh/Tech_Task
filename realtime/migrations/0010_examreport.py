from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("Home", "0026_exam_integrity_and_remove_mark"),
        ("realtime", "0009_examsession_evidence_count"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ExamReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("QUEUED", "Queued"), ("PROCESSING", "Processing"), ("READY", "Ready"), ("FAILED", "Failed")], default="QUEUED", max_length=20)),
                ("file", models.FileField(blank=True, null=True, upload_to="exam_reports/")),
                ("error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("exam", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports", to="Home.exam")),
                ("requested_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="requested_exam_reports", to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
