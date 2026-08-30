from django.contrib import admin
from .models import ExamAuditLog, ExamReport

admin.site.register(ExamAuditLog)
admin.site.register(ExamReport)
