from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from Home.models import Exam, ExamAttempt, Answer, Response, Mark, ProctorEmail
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from agora_token_builder import RtcTokenBuilder
import time
from django.conf import settings
from .services.phone_detector import (
    get_phone_session,
    decode_base64_image,
    preprocess_image,
    detect_phone_from_output
)


@login_required
def test_with_chat(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not request.user.groups.filter(name="Student").exists():
        return HttpResponseForbidden("Only students can attempt an exam.")
    if not exam.examinees.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("You are not assigned to this exam.")

    current_time = timezone.now()
    if current_time < exam.start_time or current_time > exam.end_time:
        return HttpResponseForbidden("This exam is not currently available.")

    questions = exam.questions.all()
    attempt, _ = ExamAttempt.objects.get_or_create(exam=exam, student=request.user)
    if attempt.status in (ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.TERMINATED):
        return redirect('test_end', exam_id=exam.id)

    if request.method == 'POST':
        with transaction.atomic():
            attempt = ExamAttempt.objects.select_for_update().get(pk=attempt.pk)
            if attempt.status in (ExamAttempt.Status.SUBMITTED, ExamAttempt.Status.TERMINATED):
                return redirect('test_end', exam_id=exam.id)
            if not attempt.started_at:
                attempt.started_at = timezone.now()
                attempt.status = ExamAttempt.Status.IN_PROGRESS
                attempt.save(update_fields=["started_at", "status"])

            total_marks = 0
            responses = []
            for question in questions:
                answer_id = request.POST.get(f'answer_{question.id}')
                if not answer_id:
                    continue
                try:
                    answer = question.answers.get(pk=int(answer_id))
                except (ValueError, Answer.DoesNotExist):
                    return JsonResponse({"error": "Invalid answer selection."}, status=400)
                responses.append(Response(
                    attempt=attempt, question=question, exam=exam,
                    student=request.user, text=answer.text
                ))
                total_marks += int(answer.is_correct)

            attempt.responses.all().delete()
            Response.objects.bulk_create(responses)
            Mark.objects.update_or_create(
                attempt=attempt,
                defaults={"exam": exam, "user": request.user,
                          "marks": total_marks, "company": exam.company},
            )
            attempt.status = ExamAttempt.Status.SUBMITTED
            attempt.score = total_marks
            attempt.submitted_at = timezone.now()
            attempt.save(update_fields=["status", "score", "submitted_at"])

        return redirect('test_end', exam_id=exam.id)

    return render(request, 'test.html', {
        'exam': exam,
        'questions': questions,
        'is_proctor': False,
    })
    
  
@login_required
def proctor(request, exam_id, session_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    is_proctor = ProctorEmail.objects.filter(
        email=request.user.email, submitted_by=exam.company
    ).exists()

    if not is_proctor:
        return HttpResponseForbidden("You are not authorized to access this page.")

    return render(
        request,
        "proctor.html",
        {
            'exam_id': exam_id,
            'session_id': session_id
        }
    )


@login_required
def proctor_dash(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    is_proctor = ProctorEmail.objects.filter(
        email=request.user.email, submitted_by=exam.company
    ).exists()

    if not is_proctor:
        return HttpResponseForbidden("You are not authorized to access this page.")

    return render(
        request,
        "pdash.html",
        {
            'exam_id': exam_id
        }
    )



@login_required
def test_end(request,exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not exam.examinees.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("You are not assigned to this exam.")
    return render(request, 'test_end.html')

@login_required
def get_remaining_time(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    if not exam.examinees.filter(pk=request.user.pk).exists():
        return JsonResponse({"error": "not assigned"}, status=403)

    with transaction.atomic():
        attempt, _ = ExamAttempt.objects.select_for_update().get_or_create(
            exam=exam, student=request.user
        )
        if not attempt.started_at:
            attempt.started_at = timezone.now()
            attempt.status = ExamAttempt.Status.IN_PROGRESS
            attempt.save(update_fields=["started_at", "status"])

    deadline = min(
        attempt.started_at + timedelta(minutes=exam.duration),
        exam.end_time,
    )
    remaining_time = max(0, (deadline - timezone.now()).total_seconds())
    if remaining_time == 0 and attempt.status == ExamAttempt.Status.IN_PROGRESS:
        ExamAttempt.objects.filter(
            pk=attempt.pk, status=ExamAttempt.Status.IN_PROGRESS
        ).update(status=ExamAttempt.Status.TERMINATED, submitted_at=timezone.now())
    
    return JsonResponse({"remaining_time": remaining_time})


def get_agora_token(request, exam_id):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "unauth"}, status=401)

    exam = get_object_or_404(Exam, pk=exam_id)
    is_student = exam.examinees.filter(pk=user.pk).exists()
    is_proctor = (
        user.groups.filter(name="Proctor").exists()
        and ProctorEmail.objects.filter(email=user.email, submitted_by=exam.company).exists()
    )
    if not (is_student or is_proctor or user == exam.company):
        return JsonResponse({"error": "forbidden"}, status=403)

    app_id = settings.AGORA_APP_ID
    app_cert = settings.AGORA_APP_CERT

    channel_name = f"exam_{exam_id}"
    uid = user.id  

    expiration = int(time.time()) + 3600

    token = RtcTokenBuilder.buildTokenWithUid(
        app_id,
        app_cert,
        channel_name,
        uid,
        1,  
        expiration
    )

    return JsonResponse({
        "token": token,
        "appId": app_id,
        "channel": channel_name,
        "uid": uid
    })


from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .services.phone_detector import (
    decode_base64_image
)

@login_required
@require_POST
def detect_phone(request):

    if not request.user.groups.filter(name="Student").exists():
        return JsonResponse({"error": "forbidden"}, status=403)
    if int(request.META.get("CONTENT_LENGTH") or 0) > 750_000:
        return JsonResponse({"error": "image too large"}, status=413)

    image_b64 = request.POST.get(
        "image"
    )
    if not image_b64:

        return JsonResponse(
        {
            "phone_detected": False,
            "confidence": 0
        },
        status=400
    )

    img = decode_base64_image(
        image_b64
    )

    input_tensor = preprocess_image(
        img
    )

    outputs = get_phone_session().run(
        None,
        {
            "images":
            input_tensor
        }
    )

    phone_detected, confidence = (
        detect_phone_from_output(
            outputs
        )
    )
    print(
    "[PHONE DETECTED]",
    phone_detected,
    confidence
)
    return JsonResponse({
        "phone_detected":
            phone_detected,

        "confidence":
            confidence
    })

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet
from .models import ExamSession, ExamAuditLog

@login_required
def generate_report(request, exam_id):

    exam = get_object_or_404(Exam, pk=exam_id)
    is_authorized = request.user == exam.company or ProctorEmail.objects.filter(
        email=request.user.email, submitted_by=exam.company
    ).exists()
    if not is_authorized:
        return HttpResponseForbidden("You are not authorized to view this report.")

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="exam_{exam_id}_report.pdf"'

    pdf = SimpleDocTemplate(response)
    styles = getSampleStyleSheet()

    story = [
        Paragraph(f"Exam {exam_id} Proctoring Report", styles["Title"]),
        Spacer(1, 20)
    ]

    for session in ExamSession.objects.filter(exam_id=exam_id).select_related("user"):

        story.extend([
            Paragraph(f"Student: {session.user.username}", styles["Heading2"]),
            Paragraph(f"Session ID: {session.session_id}", styles["Normal"]),
            Paragraph(f"Status: {'Active' if session.is_active else 'Inactive'}", styles["Normal"]),
            Paragraph(f"Violations: {session.violation_count}", styles["Normal"]),
            Paragraph(f"Risk Score: {session.risk_score}", styles["Normal"]),
            Paragraph(f"Latest Event: {session.latest_event}", styles["Normal"]),
            Spacer(1, 10),
            Paragraph("Timeline", styles["Heading3"])
        ])

        logs = ExamAuditLog.objects.filter(
            session_id=session.session_id
        ).order_by("timestamp")

        for log in logs:

            story.append(
                Paragraph(
                    f"{log.timestamp:%H:%M:%S} - {log.event_type} (Severity {log.severity})",
                    styles["Normal"]
                )
            )

            if log.evidence_image:

                try:

                    story.append(
                        Image(log.evidence_image.path,width=180,height=120))

                    story.append(Spacer(1, 10))

                except Exception:
                    pass

        story.extend([Spacer(1, 20),PageBreak()])

    pdf.build(story)
    return response
