from django.contrib import admin
from .models import Exam, Question, Answer, Feedback, Response, ProctorEmail, Timer, StudentProfile
from django.contrib import admin



admin.site.register(Exam)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Feedback)
admin.site.register(Response)
admin.site.register(ProctorEmail)
admin.site.register(Timer)
admin.site.register(StudentProfile)

admin.site.site_header = "Exam Platform Admin"
admin.site.site_title = "Exam Admin"
admin.site.index_title = "System Control Panel"

