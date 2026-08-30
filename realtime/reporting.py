from io import BytesIO

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer

from .models import ExamAuditLog, ExamSession


def build_report_bytes(exam):
    output = BytesIO()
    pdf = SimpleDocTemplate(output)
    styles = getSampleStyleSheet()
    evidence_streams = []

    story = [
        Paragraph(f"{exam.title} Proctoring Report", styles["Title"]),
        Spacer(1, 20),
    ]

    sessions = ExamSession.objects.filter(exam=exam).select_related("user")
    for session in sessions:
        story.extend([
            Paragraph(f"Student: {session.user.username}", styles["Heading2"]),
            Paragraph(f"Session ID: {session.session_id}", styles["Normal"]),
            Paragraph(f"Status: {'Active' if session.is_active else 'Inactive'}", styles["Normal"]),
            Paragraph(f"Violations: {session.violation_count}", styles["Normal"]),
            Paragraph(f"Risk Score: {session.risk_score}", styles["Normal"]),
            Paragraph(f"Latest Event: {session.latest_event}", styles["Normal"]),
            Spacer(1, 10),
            Paragraph("Timeline", styles["Heading3"]),
        ])

        logs = ExamAuditLog.objects.filter(
            exam=exam,
            session_id=session.session_id,
        ).order_by("timestamp")
        for log in logs:
            story.append(Paragraph(
                f"{log.timestamp:%H:%M:%S} - {log.event_type} (Severity {log.severity})",
                styles["Normal"],
            ))
            if log.evidence_image:
                try:
                    with log.evidence_image.open("rb") as evidence_file:
                        evidence_stream = BytesIO(evidence_file.read())
                    evidence_streams.append(evidence_stream)
                    story.extend([
                        Image(evidence_stream, width=180, height=120),
                        Spacer(1, 10),
                    ])
                except (OSError, ValueError):
                    continue

        story.extend([Spacer(1, 20), PageBreak()])

    pdf.build(story)
    return output.getvalue()
