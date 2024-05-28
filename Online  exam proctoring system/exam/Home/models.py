
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser

class Exam(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()        
    duration = models.IntegerField() 
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exams')

class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    OBJECTIVE = 'Objective'
    SUBJECTIVE = 'Subjective'
    QUESTION_TYPE_CHOICES = [
        (OBJECTIVE, 'Objective'),
        (SUBJECTIVE, 'Subjective'),
    ]
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
class Feedback(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])



class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('COMPANY', 'Company'),
        ('STUDENT', 'Student'),
        ('PROCTOR', 'Proctor'),
    )
    
    role = models.CharField(max_length=100, choices=ROLE_CHOICES)
    groups = models.ManyToManyField('auth.Group', related_name='customuser_set', blank=True, verbose_name='groups')
    user_permissions = models.ManyToManyField('auth.Permission', related_name='customuser_set', blank=True, verbose_name='user permissions')


class Response(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    text = models.TextField()

    def __str__(self):
        return f"Response for question: {self.question.text}"