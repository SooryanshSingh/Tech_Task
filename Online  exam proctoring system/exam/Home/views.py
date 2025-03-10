from django.contrib.auth.models import Group
from django.views.decorators.cache import cache_control
from .models import Exam,Exam, Question, Answer
from django import forms
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import QuestionForm, AnswerForm, ExamForm
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
    exams = Exam.objects.all()
    
    return render(request, 'exam_list.html', {'exams': exams})


def exam_detail(request, exam_id):
    exam = Exam.objects.get(pk=exam_id)
    return render(request, 'exam_list.html', {'exam': exam})

def exam_create(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.company = request.user
            exam.save()
            return redirect('exam_list')
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
    exam = get_object_or_404(Exam, pk=exam_id)
    
    if exam.company != request.user:
        messages.error(request, "You do not have permission to delete this exam.")
        return redirect('exam_list')  
    if request.method == 'POST':
        exam.delete()
        return redirect('exam_list')

    return render(request, 'exam_list.html', {'exam': exam})



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
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            question.save()
            return redirect('question_list', exam_id=exam_id)
    else:
        form = QuestionForm()
    return render(request, 'question_create.html', {'form': form, 'exam': exam}) 



def question_update(request, exam_id, question_id):
    try:
        exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
        question = get_object_or_404(Question, pk=question_id, exam=exam)
    except:
        return redirect(reverse('questions_list', kwargs={'exam_id': exam_id}))
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('question_list', exam_id=exam_id)
    else:
        form = QuestionForm(instance=question)
    return render(request, 'question_update.html', {'question': question,'form': form, 'exam': exam, 'question_id': question_id})

def question_delete(request, exam_id, question_id):
    exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
    question = get_object_or_404(Question, pk=question_id, exam=exam)
    if request.method == 'POST':
        question.delete()
        return redirect('question_list', exam_id=exam_id)
    return render(request, 'question_list.html', {'question': question, 'exam': exam})


def answer_list(request, exam_id, question_id):
    exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
    question = get_object_or_404(Question, pk=question_id)
    answers = Answer.objects.filter(question=question)
    return render(request, 'answer_list.html', {'answers': answers, 'question': question, 'exam_id': exam_id})


def answer_detail(request, exam_id, question_id, answer_id):
    answer = get_object_or_404(Answer, pk=answer_id)
    return render(request, 'answer_list.html', {'answer': answer})


def answer_create(request, exam_id, question_id):
    exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
    question = get_object_or_404(Question, pk=question_id, exam=exam)
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.save()
            return redirect('answer_list', exam_id=exam_id, question_id=question_id)
    else:
        form = AnswerForm()
    return render(request, 'answer_create.html', {'form': form, 'question': question, 'exam': exam})


def answer_update(request, exam_id, question_id, answer_id):
    try:
        exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
        question = get_object_or_404(Question, pk=question_id, exam=exam)
        answer = get_object_or_404(Answer, pk=answer_id, question=question)
    except:
        return redirect(reverse('answers_list', kwargs={'exam_id': exam_id, 'question_id': question_id}))
    if request.method == 'POST':
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            return redirect('answer_list', exam_id=exam_id, question_id=question_id)
    else:
        form = AnswerForm(instance=answer)
    return render(request, 'answer_update.html', {'form': form, 'question': question, 'exam_id': exam_id})


def answer_delete(request, exam_id, question_id, answer_id):
    exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
    question = get_object_or_404(Question, pk=question_id, exam=exam)
    answer = get_object_or_404(Answer, pk=answer_id, question=question)
    if request.method == 'POST':
        answer.delete()
        return redirect('answer_list', exam_id=exam_id, question_id=question_id)
    return render(request, 'answer_list.html', {'answer': answer, 'question': question, 'exam_id': exam_id})