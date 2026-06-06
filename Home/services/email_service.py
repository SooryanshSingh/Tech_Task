
from django.core.mail import send_mail

def send_exam_invite(
    email,
    invite_link
):

    send_mail(
        "Exam Invitation",

        f"You have been invited.\n\n{invite_link}",

        None,

        [email]
    )