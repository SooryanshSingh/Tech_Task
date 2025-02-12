


from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now

class Exam(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exams')
    examinees = models.ManyToManyField(User, related_name='assigned_exams', blank=True)
    start_time = models.DateTimeField(null=False, blank=False)
    end_time = models.DateTimeField(null=False, blank=False)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    attempted = models.BooleanField(default=False)  


    def __str__(self):
        return self.title

class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
class Feedback(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='feedbacks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    rating = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])

class Response(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='responses')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='responses')
    text = models.TextField()

    def __str__(self):
        return f"Response for question: {self.question.text} by {self.student.username}"
class Mark(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='marks')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    marks = models.IntegerField(default=0)

class ProctorEmail(models.Model):
    email = models.EmailField(unique=True)
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proctor_emails')

    def __str__(self):
        return self.email




class Timer(models.Model):
    exam = models.OneToOneField(Exam, on_delete=models.CASCADE, related_name="timer")
    start_time = models.DateTimeField(null=True, blank=True)

    def start_timer(self):
        """Starts the timer when the first user begins the exam."""
        if not self.start_time:
            self.start_time = now()
            self.save()

    def get_remaining_time(self):
        """Returns remaining time in seconds. If not started, return full duration."""
        if not self.start_time:
            return self.exam.duration * 60  # Full duration in seconds

        elapsed_time = (now() - self.start_time).total_seconds()
        return max(0, self.exam.duration * 60 - elapsed_time)
