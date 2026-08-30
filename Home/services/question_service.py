from django.core.exceptions import ValidationError
from django.db import transaction

from Home.models import Answer, Exam, Question


OPTION_KEYS = ("A", "B", "C", "D")


def _option_values(cleaned_data):
    values = [
        cleaned_data[f"option_{key.lower()}"].strip()
        for key in OPTION_KEYS
    ]
    if len(values) != 4 or any(not value for value in values):
        raise ValidationError("Exactly four non-empty answers are required.")
    if len({value.casefold() for value in values}) != 4:
        raise ValidationError("Answer options must be unique.")
    return values


@transaction.atomic
def save_question_with_answers(*, exam, cleaned_data, question=None):
    locked_exam = Exam.objects.select_for_update().get(pk=exam.pk)
    locked_exam.assert_questions_editable()

    values = _option_values(cleaned_data)
    correct_option = cleaned_data["correct_option"].upper()
    if correct_option not in OPTION_KEYS:
        raise ValidationError("A valid correct answer is required.")

    if question is None:
        question = Question.objects.create(
            exam=locked_exam,
            text=cleaned_data["text"],
        )
    else:
        question = Question.objects.select_for_update().get(
            pk=question.pk,
            exam=locked_exam,
        )
        question.text = cleaned_data["text"]
        question.save(update_fields=["text"])
        question.answers.all().delete()

    Answer.objects.bulk_create(
        [
            Answer(
                question=question,
                text=value,
                is_correct=(key == correct_option),
            )
            for key, value in zip(OPTION_KEYS, values, strict=True)
        ]
    )
    return question


@transaction.atomic
def delete_question(*, exam, question):
    locked_exam = Exam.objects.select_for_update().get(pk=exam.pk)
    locked_exam.assert_questions_editable()
    Question.objects.filter(pk=question.pk, exam=locked_exam).delete()
