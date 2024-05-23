from .models import Exam,Exam, Question, Answer
from django import forms
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import CustomUserCreationForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import QuestionForm, AnswerForm

def home(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

def login_user(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home'))                           
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, "Invalid information. Please try again")
    return render(request, 'login.html', {})

def logout_user(request):
    logout(request)
    return redirect('home')

def signup(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('home'))                           
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                return redirect('signup')
    else:
        form = CustomUserCreationForm()
        return render(request, 'signup.html', {'form': form})


def exam_create(request):
    if request.method == 'POST':
        form = forms.ModelForm(request.POST)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.company = request.user
            exam.save()
            return redirect('', exam_id=exam.pk)
    else:
        form = forms.ModelForm()
    return render(request, '', {'form': form})

def exam_update(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
    if request.method == 'POST':
        form = forms.ModelForm(request.POST, instance=exam)
        if form.is_valid():
            exam = form.save(commit=False)
            exam.company = request.user
            exam.save()
            return redirect('', exam_id=exam.pk)
    else:
        form = forms.ModelForm(instance=exam)
    return render(request, '', {'form': form})


def question_create(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            question.save()
            return redirect('', exam_id=exam_id)
    else:
        form = QuestionForm()
    return render(request, '', {'form': form, 'exam': exam})

def question_update(request, exam_id, question_id):
    exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
    question = get_object_or_404(Question, pk=question_id, exam=exam)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            return redirect('', exam_id=exam_id)
    else:
        form = QuestionForm(instance=question)
    return render(request, '', {'form': form, 'exam': exam})

def question_delete(request, exam_id, question_id):
    exam = get_object_or_404(Exam, pk=exam_id, company=request.user)
    question = get_object_or_404(Question, pk=question_id, exam=exam)
    if request.method == 'POST':
        question.delete()
        return redirect('exam_detail', exam_id=exam_id)
    return render(request, '', {'question': question, 'exam': exam})

