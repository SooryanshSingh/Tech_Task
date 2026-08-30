from django.db import migrations, models


def populate_evidence_counts(apps, schema_editor):
    ExamSession = apps.get_model("realtime", "ExamSession")
    ExamAuditLog = apps.get_model("realtime", "ExamAuditLog")

    for session in ExamSession.objects.iterator():
        evidence_count = (
            ExamAuditLog.objects.filter(session_id=session.session_id)
            .exclude(evidence_image="")
            .exclude(evidence_image__isnull=True)
            .count()
        )
        ExamSession.objects.filter(pk=session.pk).update(
            evidence_count=evidence_count
        )


class Migration(migrations.Migration):
    dependencies = [
        ("realtime", "0008_examsession"),
    ]

    operations = [
        migrations.AddField(
            model_name="examsession",
            name="evidence_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(populate_evidence_counts, migrations.RunPython.noop),
    ]
