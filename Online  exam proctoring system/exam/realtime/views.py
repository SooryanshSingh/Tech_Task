from django.shortcuts import render, redirect, get_object_or_404
from Home.models import Exam, Question, Answer, Response, Mark
from django.contrib.auth.decorators import login_required

@login_required
def test_with_chat(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    questions = exam.questions.all()
    is_proctor = request.user.groups.filter(name='Proctor').exists()

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

        return redirect('home')
    
    return render(request, 'test.html', {
        'exam': exam,
        'questions': questions,
        'room_name': exam_id,
        'answers': {},
        'is_proctor': is_proctor,
    })
