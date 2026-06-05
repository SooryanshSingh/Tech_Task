from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from Home.models import Exam, Answer, Response, Mark, Timer
from django.http import JsonResponse
from django.utils.timezone import now
from agora_token_builder import RtcTokenBuilder
import time
from django.conf import settings
from .services.phone_detector import (
    session,
    decode_base64_image,
    preprocess_image,
    detect_phone_from_output
)


@login_required
def test_with_chat(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()
    is_proctor = request.user.groups.filter(name='Proctor').exists()

    if exam.attempted:
        return redirect('test_end', exam_id=exam.id)

    if request.method == 'POST':
        total_marks = 0

        for question in questions:
            answer_id = request.POST.get(f'answer_{question.id}')

            if not answer_id:
                continue

            answer = get_object_or_404(Answer, pk=int(answer_id))

            Response.objects.create(
                question=question,
                exam=exam,
                student=request.user,
                text=answer.text
            )

            if answer.is_correct:
                total_marks += 1

        Mark.objects.create(
            exam=exam,
            user=request.user,
            marks=total_marks,
            company=exam.company
        )

        exam.attempted = True
        exam.save(update_fields=["attempted"])

        return redirect('test_end', exam_id=exam.id)

    return render(request, 'test.html', {
        'exam': exam,
        'questions': questions,
        'is_proctor': is_proctor,
    })
    
  
@login_required
def proctor(request, exam_id, session_id):
    is_proctor = request.user.groups.filter(name='Proctor').exists()

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
    is_proctor = request.user.groups.filter(name='Proctor').exists()

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
    exam.attempted = True
    exam.save()

  

    return render(request, 'test_end.html')

def get_remaining_time(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    timer, created = Timer.objects.get_or_create(exam=exam)

    if not timer.start_time:
        timer.start_time = now()
        timer.save()

    remaining_time = timer.get_remaining_time()
    
    return JsonResponse({"remaining_time": remaining_time})


def get_agora_token(request, exam_id):
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({"error": "unauth"}, status=401)

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
from django.views.decorators.csrf import csrf_exempt

from .services.phone_detector import session
from .services.phone_detector import (
    decode_base64_image
)

@csrf_exempt
@require_POST
def detect_phone(request):

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

    outputs = session.run(
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