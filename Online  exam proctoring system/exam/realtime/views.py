from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from Home.models import Exam, Answer, Response, Mark, Timer
from django.http import JsonResponse
from django.utils.timezone import now

@login_required
def test_with_chat(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()
    is_proctor = request.user.groups.filter(name='Proctor').exists()
    if exam.attempted:
        return redirect('test_end', exam_id=exam.id) 
    
   
    if request.method == 'POST':
        total_marks = 0
        answers = {}

        for question in questions:
            answer_id = request.POST.get(f'answer_{question.id}')
            if answer_id:
                answers[question.id] = int(answer_id)
            else:
                answers[question.id] = None
        
        for question_id, answer_id in answers.items():
            if answer_id is None:
                return render(request, 'test.html', {
                    'exam': exam,
                    'questions': questions,
                    'error_message': 'You must select an answer for each question.',
                    'room_name': exam_id,
                    'answers': answers,
                    'is_proctor': is_proctor,
                })

            answer = get_object_or_404(Answer, pk=answer_id)
            response_text = answer.text
            Response.objects.create(
                question_id=question_id, 
                exam=exam, 
                student=request.user, 
                text=response_text
            )

            if answer.is_correct:
                total_marks += 1
        
        Mark.objects.create(exam=exam, user=request.user, marks=total_marks)


        return redirect('test_end', exam_id=exam.id) 
    
    return render(request, 'test.html', {
        'exam': exam,
        'questions': questions,
        'room_name': exam_id,
        'answers': {},
        'is_proctor': is_proctor,
    })

@login_required
def proctor(request,exam_id):
        is_proctor = request.user.groups.filter(name='Proctor').exists()

        if is_proctor:

            return render(request,"proctor.html",{'exam_id':exam_id})

        





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



