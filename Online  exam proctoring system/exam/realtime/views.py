from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from Home.models import Exam, Question, Answer, Response
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from Home.models import Mark

def test_with_chat(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()

    if request.method == 'POST':
        total_marks = 0
        for question in questions:
            answer_id = request.POST.get(f'answer_{question.id}')
            if not answer_id:
                return render(request, 'test.html', {
                    'exam': exam,
                    'questions': questions,
                    'error_message': 'You must select an answer for each question.',
                    'room_name': exam_id,
                })
            answer = get_object_or_404(Answer, pk=answer_id)
            response_text = answer.text
            Response.objects.create(question=question, exam=exam, text=response_text)


            if answer.is_correct:
                total_marks += 1  


        mark = Mark.objects.create(exam=exam, user=request.user, marks=total_marks)


        message = request.POST.get('chat_message')
        if message and message.strip():
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{exam_id}",
                {
                    "type": "chat.message",
                    "message": message,
                }
            )

        return redirect('home')

    return render(request, 'test.html', {
        'exam': exam,
        'questions': questions,
        'room_name': exam_id,
    })

