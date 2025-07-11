from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Exam, Question, Answer, ProctorEmail

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


class QuestionWithAnswersForm(forms.Form):
    text = forms.CharField(label="Question Text", widget=forms.Textarea)

    option_a = forms.CharField(label="Option A")
    option_b = forms.CharField(label="Option B")
    option_c = forms.CharField(label="Option C")
    option_d = forms.CharField(label="Option D")

    CORRECT_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]
    correct_option = forms.ChoiceField(choices=CORRECT_CHOICES, widget=forms.RadioSelect)

class ExamForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=True
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        ),
        input_formats=['%Y-%m-%dT%H:%M'],
        required=True
    )
    duration = forms.IntegerField(help_text="Duration in minutes")
    email_list = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Use comma"
    )

    class Meta:
        model = Exam
        fields = ['title', 'description', 'start_time', 'end_time', 'duration', 'email_list']





class ProctorEmailForm(forms.ModelForm):
    class Meta:
        model = ProctorEmail
        fields = ['email']

class BaseQuestionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

