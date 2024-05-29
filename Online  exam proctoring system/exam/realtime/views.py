from django.shortcuts import render, get_object_or_404, redirect
from Home.models import Exam
from Home.models import Response

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
        return redirect('feedback.html')  
    
    return render(request, 'test.html', {
        'exam': exam,
        'questions': questions,
        'room_name': exam_id, 
    })

