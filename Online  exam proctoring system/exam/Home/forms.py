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

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text', 'is_correct']


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text']

AnswerFormSet = inlineformset_factory(
    Question,  # Parent model
    Answer,    # Child model
    form=AnswerForm,
    fields=['text', 'is_correct'],
    extra=1,   # Number of extra forms
    can_delete=True,
    min_num=1, # Minimum number of forms
    validate_min=True,
)

class ExamForm(forms.ModelForm):
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=False
    )
    duration = forms.IntegerField(help_text="Duration in minutes")  # New field

    class Meta:
        model = Exam
        fields = ['title', 'description', 'start_time', 'end_time', 'duration']


class ProctorEmailForm(forms.ModelForm):
    class Meta:
        model = ProctorEmail
        fields = ['email']

class BaseQuestionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

QuestionFormSet = inlineformset_factory(
    Exam,        # Parent model (you may change this to suit your project)
    Question,    # Child model
    formset=BaseQuestionFormSet,
    form=QuestionForm,
    fields=['text'],
    extra=1,     # Number of extra forms
    can_delete=True,
    min_num=1,   # Minimum number of forms
    validate_min=True,
)
