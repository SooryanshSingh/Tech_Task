from django.contrib.auth.models import Group, User
from django.views.decorators.cache import cache_control
from .models import Exam,Exam, Question, Answer
from django import forms
from django.http import JsonResponse
import json

from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import QuestionWithAnswersForm
from .forms import ExamForm, QuestionForm, AnswerForm
from .forms import ProctorEmailForm 
from .models import ProctorEmail
from django.utils import timezone  

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    is_company = request.user.groups.filter(name='Company').exists()
    is_proctor = request.user.groups.filter(name='Company').exists()

    return render(request, 'home.html', {'is_company': is_company,'is_proctor':is_proctor})

def about(request):
    return render(request, 'about.html')
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout_user(request):
    logout(request)
    return redirect('home')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login_user(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Student').exists():
            return redirect('dashboard')
        elif request.user.groups.filter(name='Company').exists() and not request.user.groups.filter(name='Proctor').exists():
            return redirect('company_dashboard')
        elif request.user.groups.filter(name='Proctor').exists():
            return redirect('proctor_dashboard')
        else:
            return redirect('home')

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.groups.filter(name='Student').exists():
                return redirect('dashboard')
            elif user.groups.filter(name='Company').exists() and not user.groups.filter(name='Proctor').exists():
                return redirect('company_dashboard')
            elif user.groups.filter(name='Proctor').exists():
                return redirect('proctor_dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, "Invalid information. Please try again")

    return render(request, 'login.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def signup(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Student').exists():
            return redirect('dashboard')
        elif request.user.groups.filter(name='Company').exists() and not request.user.groups.filter(name='Proctor').exists():
            return redirect('company_dashboard')
        elif request.user.groups.filter(name='Proctor').exists():
            return redirect('proctor_dashboard')
        else:
            return redirect('home')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            role = form.cleaned_data['role']
            if role == 'Company':
                group = Group.objects.get(name='Company')
                user.groups.add(group)
            elif role == 'Student':
                group = Group.objects.get(name='Student')
                user.groups.add(group)

            if ProctorEmail.objects.filter(email=user.email).exists():
                group = Group.objects.get(name='Proctor')
                user.groups.add(group)

            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if user.groups.filter(name='Student').exists():
                    return redirect('dashboard')
                elif user.groups.filter(name='Company').exists() and not user.groups.filter(name='Proctor').exists():
                    return redirect('company_dashboard')
                elif user.groups.filter(name='Proctor').exists():
                    return redirect('proctor_dashboard')
                else:
                    return redirect('home')
            else:
                return redirect('signup')
    else:
        form = CustomUserCreationForm()

    return render(request, 'signup.html', {'form': form})



def dashboard(request):
    user = request.user
    current_time = timezone.now()
    
    assigned_exams = Exam.objects.filter(examinees=user)

    for exam in assigned_exams:
        exam.has_started = exam.start_time <= current_time
        exam.has_ended = exam.end_time < current_time

    
    context = {
        'user': user,
        'assigned_exams': assigned_exams,
        'current_time': current_time,
    }

    return render(request, 'dashboard.html', context)

def company_dashboard(request):
    if request.method == 'POST':
        form = ProctorEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            ProctorEmail.objects.create(email=email, submitted_by=request.user)
            form = ProctorEmailForm()  # Clear the form after submission
            return render(request, 'company_dashboard.html', {
                'form': form, 
                'success': True,
                'total_exams': Exam.objects.filter(company=request.user).count(),
                'total_proctors': ProctorEmail.objects.filter(submitted_by=request.user).count()
            })
    else:
        form = ProctorEmailForm()

    return render(request, 'company_dashboard.html', {
        'form': form,
        'total_exams': Exam.objects.filter(company=request.user).count(),
        'total_proctors': ProctorEmail.objects.filter(submitted_by=request.user).count()
    })
  
def proctor_dashboard(request):
    if request.user.groups.filter(name='Proctor').exists():
        company = ProctorEmail.objects.get(email=request.user.email).submitted_by
        exams = Exam.objects.filter(company=company)
        context = {
            'exams': exams,
            'company': company,
        }
        return render(request, 'proctor_dashboard.html', context)
    else:
        return redirect('home')
def marks_view(request):
    if request.user.groups.filter(name='Company').exists():
        exams = Exam.objects.filter(company=request.user)
        context = {'exams': exams}
        return render(request, 'marks.html', context)
    else:
        return redirect('home')
        
        
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def exam_list(request):
    if request.user.is_authenticated and request.user.groups.filter(name='Company').exists():
        exams = Exam.objects.filter(company=request.user)
    else:
        exams = None
    return render(request, 'exam_list.html', {'exams': exams})


def exam_detail(request, exam_id):
    exam = Exam.objects.get(pk=exam_id)
    return render(request, 'exam_list.html', {'exam': exam})


def exam_create(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        exam_data_list = data.get('exams', [])
        created_exams = []

        for exam_data in exam_data_list:
            form = ExamForm(exam_data)
            if form.is_valid():
                exam = form.save(commit=False)
                exam.company = request.user
                exam.save()

                email_list = form.cleaned_data.get('email_list', '')
                raw_emails = email_list.split(',')

                for email in raw_emails:
                    email = email.strip().lower()
                    if not email:
                        continue

                    user = User.objects.filter(email=email).first()
                    if user:
                        exam.examinees.add(user)
                    else:
                        print(f"No user found with email: {email}")


                created_exams.append(exam.id)
            else:
                return JsonResponse({
                    'error': 'Invalid exam entry',
                    'details': form.errors
                }, status=400)

        return JsonResponse({'message': f'{len(created_exams)} exams created successfully', 'ids': created_exams})

    else:  
        form = ExamForm()
        return render(request, 'exam_create.html', {'form': form})
def exam_update(request, exam_id):
    try:
        exam = get_object_or_404(Exam, pk=exam_id)

    except:
        return redirect('exam_list') 
    if exam.company != request.user:
        messages.error(request, "You do not have permission to update this exam.")
        return redirect('exam_list')  

    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.company = request.user
            exam.save()
            return redirect('exam_list')
    else:
        form = ExamForm(instance=exam)
    
    return render(request, 'exam_update.html', {'form': form, 'exam': exam})


def exam_delete(request, exam_id):
    if request.method == 'POST':
        exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
        exam.delete()
        messages.success(request, f'Exam "{exam.title}" deleted successfully.')
        return redirect('exam_list')  
    messages.error(request, 'Invalid request method.')
    return redirect('exam_list')

def question_list(request, exam_id=None):
    if exam_id is not None:
        exam = get_object_or_404(Exam, pk=exam_id)
        if exam.company != request.user:
            messages.error(request, "You do not have permission to view questions for this exam.")
            return render(request, 'exam_list.html', {'exams': Exam.objects.all()})
        questions = Question.objects.filter(exam_id=exam_id)
    else:
        questions = Question.objects.all()
    return render(request, 'question_list.html', {'questions': questions, 'exam_id': exam_id})

def question_detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'question_list.html', {'question': question})


def question_create(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, company=request.user)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            questions_data = data.get('questions', [])
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        created_questions = []

        for i, q in enumerate(questions_data):
            form = QuestionWithAnswersForm(q)
            if form.is_valid():
                # Ensure all 4 options are present
                if not all([
                    form.cleaned_data.get('option_a'),
                    form.cleaned_data.get('option_b'),
                    form.cleaned_data.get('option_c'),
                    form.cleaned_data.get('option_d')
                ]):
                    return JsonResponse({
                        'error': f'All four options are required at index {i}.'
                    }, status=400)

                question = Question.objects.create(
                    exam=exam,
                    text=form.cleaned_data['text']
                )

                options = [
                    ('A', form.cleaned_data['option_a']),
                    ('B', form.cleaned_data['option_b']),
                    ('C', form.cleaned_data['option_c']),
                    ('D', form.cleaned_data['option_d']),
                ]

                answers = [
                    Answer(
                        question=question,
                        text=opt_text,
                        is_correct=(form.cleaned_data['correct_option'] == opt_key)
                    )
                    for opt_key, opt_text in options
                ]

                Answer.objects.bulk_create(answers)
                created_questions.append(question)

            else:
                return JsonResponse({
                    'error': f'Invalid question at index {i}',
                    'details': form.errors
                }, status=400)

        return JsonResponse({'message': f'{len(created_questions)} questions created successfully.'})

    elif request.method == 'GET':
        form = QuestionWithAnswersForm()
        return render(request, 'question_create.html', {'form': form, 'exam': exam})

    return JsonResponse({'error': 'Only POST and GET methods allowed'}, status=405)





def question_update(request, exam_id, question_id):
    exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
    question = get_object_or_404(Question, pk=question_id, exam=exam)

    if request.method == 'POST':
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)
            form = QuestionWithAnswersForm(data)
        else:
            form = QuestionWithAnswersForm(request.POST)

        if form.is_valid():
            question.text = form.cleaned_data['text']
            question.save()

            options = [
                ('A', form.cleaned_data['option_a']),
                ('B', form.cleaned_data['option_b']),
                ('C', form.cleaned_data['option_c']),
                ('D', form.cleaned_data['option_d']),
            ]

            existing_answers = list(question.answers.all().order_by('id'))

            if len(existing_answers) == 4:
                for i, (opt_key, opt_text) in enumerate(options):
                    existing_answers[i].text = opt_text
                    existing_answers[i].is_correct = (form.cleaned_data['correct_option'] == opt_key)
                    existing_answers[i].save()
            else:
                question.answers.all().delete()
                Answer.objects.bulk_create([
                    Answer(
                        question=question,
                        text=opt_text,
                        is_correct=(form.cleaned_data['correct_option'] == opt_key)
                    )
                    for opt_key, opt_text in options
                ])

            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'message': f'Question {question_id} updated successfully.'})
            else:
                return redirect('question_list', exam_id=exam.id)  
        errors = form.errors.get_json_data()
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'error': 'Invalid form', 'details': errors}, status=400)
        else:
            return render(request, 'question_update.html', {
                'form': form,
                'exam': exam,
                'question': question,
                'errors': errors
            })

    # === GET ===
    answers = list(question.answers.all().order_by('id'))
    correct_option = None

    if len(answers) == 4:
        options = ['A', 'B', 'C', 'D']
        correct_index = next((i for i, a in enumerate(answers) if a.is_correct), None)
        correct_option = options[correct_index] if correct_index is not None else None

        initial = {
            'text': question.text,
            'option_a': answers[0].text,
            'option_b': answers[1].text,
            'option_c': answers[2].text,
            'option_d': answers[3].text,
            'correct_option': correct_option
        }
    else:
        initial = {'text': question.text}

    form = QuestionWithAnswersForm(initial=initial)
    return render(request, 'question_update.html', {
        'form': form,
        'exam': exam,
        'question': question
    })


def question_delete(request, exam_id, question_id):
    exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
    question = get_object_or_404(Question, pk=question_id, exam=exam)

    if request.method == 'POST':
        question.delete()
        return redirect('question_list', exam_id=exam_id)

    return redirect('question_list', exam_id=exam_id)
