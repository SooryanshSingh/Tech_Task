from django.contrib import admin
from .models import Exam, Question, Answer, Feedback,  Response, Mark



admin.site.register(Exam)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Feedback)
admin.site.register(Response)

admin.site.register(Mark)
# Register your models here.
