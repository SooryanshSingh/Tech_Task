from datetime import timedelta

from django.db import migrations, models
from django.db.models import F, Q


def copy_marks_to_attempts(apps, schema_editor):
    ExamAttempt = apps.get_model("Home", "ExamAttempt")
    Mark = apps.get_model("Home", "Mark")

    for mark in Mark.objects.select_related("attempt").iterator():
        attempt = mark.attempt
        if attempt is None:
            attempt, _ = ExamAttempt.objects.get_or_create(
                exam_id=mark.exam_id,
                student_id=mark.user_id,
            )

        update_fields = {"score": max(0, mark.marks)}
        if attempt.status in ("NOT_STARTED", "IN_PROGRESS"):
            update_fields["status"] = "SUBMITTED"
        ExamAttempt.objects.filter(pk=attempt.pk).update(**update_fields)


def normalize_existing_exam_and_answer_data(apps, schema_editor):
    Exam = apps.get_model("Home", "Exam")
    Answer = apps.get_model("Home", "Answer")

    for exam in Exam.objects.all().iterator():
        update_fields = {}
        if exam.duration <= 0:
            update_fields["duration"] = 1
        if exam.end_time <= exam.start_time:
            update_fields["end_time"] = exam.start_time + timedelta(
                minutes=max(1, exam.duration)
            )
        if update_fields:
            Exam.objects.filter(pk=exam.pk).update(**update_fields)

    duplicate_question_ids = (
        Answer.objects.filter(is_correct=True)
        .values_list("question_id", flat=True)
        .order_by("question_id")
    )
    seen_question_ids = set()
    for question_id in duplicate_question_ids.iterator():
        if question_id in seen_question_ids:
            correct_answers = Answer.objects.filter(
                question_id=question_id,
                is_correct=True,
            ).order_by("pk")
            first_correct_id = correct_answers.values_list("pk", flat=True).first()
            correct_answers.exclude(pk=first_correct_id).update(is_correct=False)
        seen_question_ids.add(question_id)


class Migration(migrations.Migration):
    dependencies = [
        ("Home", "0025_examattempt_response_attempt_mark_attempt"),
    ]

    operations = [
        migrations.AddField(
            model_name="exam",
            name="closed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(copy_marks_to_attempts, migrations.RunPython.noop),
        migrations.DeleteModel(name="Mark"),
        migrations.RunPython(
            normalize_existing_exam_and_answer_data,
            migrations.RunPython.noop,
        ),
        migrations.AddConstraint(
            model_name="exam",
            constraint=models.CheckConstraint(
                condition=Q(end_time__gt=F("start_time")),
                name="exam_end_after_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="exam",
            constraint=models.CheckConstraint(
                condition=Q(duration__gt=0),
                name="exam_duration_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="answer",
            constraint=models.UniqueConstraint(
                condition=Q(is_correct=True),
                fields=("question",),
                name="unique_correct_answer_per_question",
            ),
        ),
    ]
