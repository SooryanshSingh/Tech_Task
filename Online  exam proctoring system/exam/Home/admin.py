from django.contrib import admin
from .models import Exam, Question, Answer, Feedback

class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'duration', 'company')
    search_fields = ('title', 'company__username')
    list_filter = ('company',)

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'text')
    search_fields = ('text', 'exam__title')
    list_filter = ('exam',)

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'text', 'is_correct')
    search_fields = ('text', 'question__text')
    list_filter = ('question', 'is_correct')

class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('exam', 'user', 'comment', 'rating')
    search_fields = ('comment', 'exam__title', 'user__username')
    list_filter = ('exam', 'user', 'rating')

admin.site.register(Exam, ExamAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(Feedback, FeedbackAdmin)
from django.contrib import admin

# Register your models here.
