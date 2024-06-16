# forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Exam,Question,Answer
from django.forms import inlineformset_factory
class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('Company', 'Company'),
        ('Student', 'Student'),
       
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')  
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for fieldname in ['username', 'password1', 'password2']:
            self.fields[fieldname].help_text = None



class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']  

class ExamForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )
    class Meta:
        model = Exam
        fields = ['title', 'description','start_time', 'end_time']
QuestionFormSet = inlineformset_factory(Exam, Question, form=QuestionForm, extra=1, can_delete=True)
AnswerFormSet = inlineformset_factory(Question, Answer, form=AnswerForm, extra=1, can_delete=True)


from .models import ProctorEmail

class ProctorEmailForm(forms.ModelForm):
    class Meta:
        model = ProctorEmail
        fields = ['email']