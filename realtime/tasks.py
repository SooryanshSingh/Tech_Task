from celery import shared_task
from django.core.files.base import ContentFile
from django.utils import timezone

from .models import ExamReport
from .reporting import build_report_bytes


@shared_task(bind=True, autoretry_for=(OSError,), retry_backoff=True, max_retries=3)
def generate_exam_report(self, report_id):
    report = ExamReport.objects.select_related("exam").get(pk=report_id)
    report.status = ExamReport.Status.PROCESSING
    report.error = ""
    report.save(update_fields=["status", "error"])

    try:
        pdf_bytes = build_report_bytes(report.exam)
        report.file.save(
            f"exam_{report.exam_id}_report_{report.pk}.pdf",
            ContentFile(pdf_bytes),
            save=False,
        )
        report.status = ExamReport.Status.READY
        report.completed_at = timezone.now()
        report.save(update_fields=["file", "status", "completed_at"])
    except Exception as exc:
        report.status = ExamReport.Status.FAILED
        report.error = str(exc)[:2000]
        report.completed_at = timezone.now()
        report.save(update_fields=["status", "error", "completed_at"])
        raise
