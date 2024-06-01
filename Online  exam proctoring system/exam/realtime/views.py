from django.shortcuts import render, get_object_or_404, redirect
from Home.models import Exam, Response
from .models import ChatMessage  

def test_with_chat(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()
    
    if request.method == 'POST':
        for question in questions:
            answer_text = request.POST.get('answer_' + str(question.id))
            if question.question_type == 'Objective':
                response = Response.objects.create(
                    question=question,
                    text=answer_text
                )
            else:
                response = Response.objects.create(
                    question=question,
                    text=answer_text
                )
        
        message = request.POST.get('chat_message')
        if message.strip():
            ChatMessage.objects.create(sender=request.user, message=message)

        return redirect('feedback.html')  
    
    return render(request, 'test.html', {
        'exam': exam,
        'questions': questions,
        'room_name': exam_id, 
    })




def chat_room(request, room_name):
    return render(request, 'chat_room.html', {
        'room_name': room_name
    })
