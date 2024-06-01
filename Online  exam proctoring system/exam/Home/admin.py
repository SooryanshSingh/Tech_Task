from django.contrib import admin
from .models import Exam, Question, Answer, Feedback,  Response



admin.site.register(Exam)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Feedback)
admin.site.register(Response)

# Register your models here.
