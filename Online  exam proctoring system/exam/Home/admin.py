from django.contrib import admin
from .models import Exam, Question, Answer, Feedback, CustomUser



admin.site.register(Exam)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Feedback)
admin.site.register(CustomUser)

# Register your models here.
