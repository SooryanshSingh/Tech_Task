# models.py

from django.db import models
from django.contrib.auth.models import User
from Home.models import Exam

class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


