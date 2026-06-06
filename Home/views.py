from django.contrib.auth.models import Group, User

from django.views.decorators.cache import cache_control
from .models import Exam,Exam, Question, Answer, Mark
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
import json
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import CustomUserCreationForm
from .forms import QuestionWithAnswersForm
from .forms import ExamForm
from .forms import ProctorEmailForm 
from .models import ProctorEmail, StudentProfile
from django.utils import timezone  
from .services.face_embedding import extract_embedding
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.urls import reverse

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def home(request):
    is_company = request.user.groups.filter(name='Company').exists()
    is_proctor = request.user.groups.filter(name='Proctor').exists()
    is_student = request.user.groups.filter(name='Student').exists()

    return render(request, 'home.html', {'is_company': is_company,'is_proctor':is_proctor,'is_student':is_student})

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

        if request.user.groups.filter(name='Company').exists() and not request.user.groups.filter(name='Proctor').exists():
            return redirect('company_dashboard')

        if request.user.groups.filter(name='Proctor').exists():
            return redirect('proctor_dashboard')

        return redirect('home')

    form = CustomUserCreationForm(
        request.POST or None,
        request.FILES or None
    )

    if request.method == "POST" and form.is_valid():

        role = form.cleaned_data['role']
        embedding = None

        if role == "Student":

            embedding = extract_embedding(
                form.cleaned_data["profile_image"]
            )

            if embedding is None:

                form.add_error(
                    "profile_image",
                    "Exactly one clear face must be visible."
                )

                return render(
                    request,
                    "signup.html",
                    {"form": form}
                )

        user = form.save(commit=False)
        user.is_active = False
        user.save()

        if role == "Test Admin":

            group, _ = Group.objects.get_or_create(
                name="Company"
            )

            user.groups.add(group)

        elif role == "Student":

            group, _ = Group.objects.get_or_create(
                name="Student"
            )

            user.groups.add(group)

            StudentProfile.objects.create(
                user=user,
                profile_image=form.cleaned_data["profile_image"],
                embedding=embedding.tolist()
            )

        if ProctorEmail.objects.filter(
            email=user.email
        ).exists():

            group, _ = Group.objects.get_or_create(
                name="Proctor"
            )

            user.groups.add(group)

        uid = urlsafe_base64_encode(
            force_bytes(user.pk)
        )

        token = default_token_generator.make_token(
            user
        )

        verify_link = request.build_absolute_uri(
            reverse(
                "verify_email",
                args=[uid, token]
            )
        )

        send_mail(
            "Verify Your Email",
            f"Click the link below to verify your account:\n\n{verify_link}",
            None,
            [user.email]
        )

        return render(
            request,
            "verification_sent.html",
            {
                "email": user.email
            }
        )

    return render(
        request,
        "signup.html",
        {"form": form}
    )
def dashboard(request):
    if not request.user.groups.filter(name='Student').exists():
        return redirect('home')

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
    if not request.user.groups.filter(name='Company').exists():
        return redirect('home')


    if request.method == 'POST':
        form = ProctorEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            ProctorEmail.objects.create(email=email, submitted_by=request.user)
            form = ProctorEmailForm()  
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
        print(request.user.email)
        
        
        company = ProctorEmail.objects.get(email=request.user.email).submitted_by
        print("OK",company)
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
        marks = Mark.objects.filter(company=request.user)
        context = {'marks': marks}

        print("This",marks)
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


from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import render
import json

from .forms import ExamForm
from .models import ExamInvite
from .services.email_service import send_exam_invite


def exam_create(request):

    if request.method == 'POST':

        try:
            data = json.loads(request.body)
            print(data)

        except json.JSONDecodeError:

            return JsonResponse(
                {'error': 'Invalid JSON'},
                status=400
            )

        exam_data_list = data.get(
            'exams',
            []
        )

        created_exams = []

        for exam_data in exam_data_list:

            form = ExamForm(exam_data)

            if not form.is_valid():

                return JsonResponse(
                    {
                        'error':
                        'Invalid exam entry',

                        'details':
                        form.errors
                    },
                    status=400
                )

            exam = form.save(commit=False)

            exam.company = request.user

            exam.save()

            email_list = form.cleaned_data.get(
                'email_list',
                ''
            )

            emails = [
                email.strip().lower()
                for email in email_list.splitlines()
                if email.strip()
            ]

            for email in emails:

                invite = ExamInvite.objects.create(
                    exam=exam,
                    email=email
                )

                invite_link = (
                    request.build_absolute_uri(
                        reverse(
                            "accept_invite",
                            args=[invite.token]
                        )
                    )
                )

                send_exam_invite(email,invite_link)

            created_exams.append(exam.id)

        print(form.errors)
        return JsonResponse(
            {
                'message':
                f'{len(created_exams)} exams created successfully',

                'ids':
                created_exams
            }
        )
        

    form = ExamForm()

    return render(
        request,
        'exam_create.html',
        {
            'form': form
        }
    )
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
                        is_correct=(form.cleaned_data['correct_option'].upper() == opt_key)
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

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from Home.models import StudentProfile
import json
import base64
import tempfile



from numpy.linalg import norm
import numpy as np

def cosine_similarity(a, b):

    return np.dot(a, b) / (
        norm(a) * norm(b)
    )

@login_required
def verify_identity(request):

    if request.method != "POST":
        return JsonResponse(
            {"verified": False},
            status=400
        )

    try:

        image_data = json.loads(request.body)["image"]

        header, encoded = image_data.split(";base64,")

        image_bytes = base64.b64decode(encoded)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:

            temp_file.write(image_bytes)
            temp_file.flush()

            live_embedding = (
                extract_embedding(
                    temp_file.name
                )
            )

        if live_embedding is None:

            return JsonResponse({
                "verified": False,
                "reason": "No face detected"
            })
        try:
            profile = StudentProfile.objects.get(user=request.user)
        except StudentProfile.DoesNotExist:

            return JsonResponse({"verified": False,"reason": "Profile not found"})


        stored_embedding = np.array(profile.embedding,dtype=np.float32)
        similarity = float(cosine_similarity(live_embedding,stored_embedding))
        print("The similarity is ",similarity)
        return JsonResponse({

            "verified":
            similarity >= 0.55,

            "similarity":
            round(similarity, 3)
        })

    except Exception as e:

        return JsonResponse(
            {
                "verified": False,
                "error": str(e)
            },
            status=500
        )
    
@login_required
@login_required
def identity_check(request, exam_id):

    exam = get_object_or_404(
        Exam,
        id=exam_id
    )

    if exam.attempted:
        return redirect("test_end",exam_id=exam.id
        )

    if not StudentProfile.objects.filter(
        user=request.user
    ).exists():

        return HttpResponseForbidden("Face profile not found.")

    return render(request,"identity_check.html",{"exam": exam}
    )    


@login_required
def accept_invite(request, token):

    invite = get_object_or_404(
        ExamInvite,
        token=token,
        used=False
    )

    invite.exam.examinees.add(
        request.user
    )

    invite.used = True
    invite.accepted_by = request.user
    invite.save()

    return redirect("dashboard")


from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model

User = get_user_model()

def verify_email(request,uidb64,token):

    try:

        uid = (urlsafe_base64_decode(uidb64).decode()
        )

        user = User.objects.get(pk=uid)

    except Exception:

        user = None

    if (user and default_token_generator.check_token(user,token)):

        user.is_active = True
        user.save()

        return redirect("login")

    return HttpResponse("Invalid verification link.")