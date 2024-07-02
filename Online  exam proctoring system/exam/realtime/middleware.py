from django.shortcuts import redirect
from Home.models import Exam

class ExamAttemptMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        exam_id = view_kwargs.get('exam_id')
        if exam_id:
            exam = Exam.objects.get(id=exam_id)
            if exam.attempted:
                return redirect('test_end')
        return None
