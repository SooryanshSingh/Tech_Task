import base64
import binascii
import json
import uuid

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from Home.models import Exam, ExamAttempt, ProctorEmail
from django.utils import timezone

from .models import (
    ExamAuditLog,
    ExamSession
)
from django.core.files.base import ContentFile


VIOLATION_WEIGHTS = {
    "TAB_SWITCH": 10,
    "FULLSCREEN_EXIT": 15,
    "NO_FACE": 20,
    "MULTIPLE_FACES": 35,
    "PHONE_DETECTED": 40,

}
MAX_EVIDENCE_BYTES = 500_000

MAX_EVIDENCE_PER_SESSION = 50

ALLOWED_EVIDENCE_EVENTS = {

    "NO_FACE",

    "MULTIPLE_FACES",

    "PHONE_DETECTED"
}

class ExamControlConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def access_role(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            return None
        exam = Exam.objects.filter(pk=self.exam_id).first()
        if not exam:
            return None
        if exam.examinees.filter(pk=user.pk).exists():
            return "student"
        if (
            user.groups.filter(name="Proctor").exists()
            and ProctorEmail.objects.filter(email=user.email, submitted_by=exam.company).exists()
        ) or user.pk == exam.company_id:
            return "proctor"
        return None

    @database_sync_to_async
    def log_event(
        self,
        event_type,
        severity=0,
        metadata=None
    ):
        ExamAuditLog.objects.create(
            exam_id=self.exam_id,

            actor=(
                self.scope["user"]
                if self.scope["user"].is_authenticated
                else None
            ),

            session_id=None,

            event_type=event_type,

            severity=severity,

            metadata=metadata or {}
        )

    @database_sync_to_async
    def terminate_exam(self):
        now = timezone.now()
        with transaction.atomic():
            exam = Exam.objects.select_for_update().get(pk=self.exam_id)
            already_closed = exam.closed_at is not None
            if not already_closed:
                exam.closed_at = now
                exam.save(update_fields=["closed_at"])

            terminated_count = ExamAttempt.objects.filter(
                exam=exam,
                status__in=(
                    ExamAttempt.Status.NOT_STARTED,
                    ExamAttempt.Status.IN_PROGRESS,
                ),
            ).update(
                status=ExamAttempt.Status.TERMINATED,
                submitted_at=now,
            )

            ExamAuditLog.objects.create(
                exam=exam,
                actor=self.scope["user"],
                event_type="EXAM_CLOSED",
                severity=100,
                metadata={
                    "exam_id": exam.pk,
                    "terminated_attempts": terminated_count,
                    "already_closed": already_closed,
                },
            )
        return terminated_count

    async def connect(self):
        self.authorized = False
        self.exam_id = self.scope['url_route']['kwargs']['exam_id']

        self.role = await self.access_role()
        if not self.role:
            await self.close(code=4403)
            return
        self.authorized = True

        self.room_group_name = f'exam_{self.exam_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if not getattr(self, "authorized", False):
            return
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):

        if self.role != "proctor":
            await self.close(code=4403)
            return

        data = json.loads(text_data)

        if data.get("type") == "close_exam":
            terminated_count = await self.terminate_exam()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type":
                    "exam_closed",
                    "terminated_attempts": terminated_count,
                }
            )

        if data.get("type") == "warn_student":

            await self.log_event(
                event_type="WARNING_SENT",
                severity=5,
                metadata={
                    "exam_id": self.exam_id
                }
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type":
                    "warning_message"
                }
            )

    async def exam_closed(self, event):

        await self.send(
            text_data=json.dumps({
                "type":
                "exam_closed",
                "terminated_attempts": event.get("terminated_attempts", 0),
            })
        )

    async def warning_message(self, event):

        await self.send(
            text_data=json.dumps({
                "type":
                "warning_message"
            })
        )


class TabMonitorConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def get_or_create_session(self):

        session, created = (
            ExamSession.objects.get_or_create(
                exam_id=self.exam_id,
                user=self.user,
                defaults={
                    "session_id": self.session_id
                }
            )
        )
        if not created:

            session.is_active = True
            session.save(
                update_fields=["is_active"]
            )

        return session    
    
    @staticmethod
    def _decode_evidence(event_type, evidence_image):
        if not evidence_image or event_type not in ALLOWED_EVIDENCE_EVENTS:
            return None
        try:
            _, encoded = evidence_image.split(";base64,", 1)
            image_bytes = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error):
            return None
        if len(image_bytes) > MAX_EVIDENCE_BYTES:
            return None
        return ContentFile(image_bytes, name=f"{uuid.uuid4()}.jpg")

    @database_sync_to_async
    def record_violation(self, session, event_type, severity, evidence_image=None):
        evidence_file = self._decode_evidence(event_type, evidence_image)

        with transaction.atomic():
            session = ExamSession.objects.select_for_update().get(pk=session.pk)
            session.violation_count += 1
            session.risk_score += severity
            session.latest_event = event_type

            if session.evidence_count >= MAX_EVIDENCE_PER_SESSION:
                evidence_file = None

            log = ExamAuditLog(
                exam_id=self.exam_id,
                actor=self.user,
                session_id=self.session_id,
                event_type=event_type,
                severity=severity,
                metadata={"risk_score": session.risk_score},
            )
            if evidence_file:
                log.evidence_image.save(evidence_file.name, evidence_file, save=False)
                session.evidence_count += 1

            log.save()
            session.save(
                update_fields=(
                    "violation_count",
                    "risk_score",
                    "latest_event",
                    "evidence_count",
                )
            )
        return session, log
    
    @database_sync_to_async
    def mark_inactive(self):

        ExamSession.objects.filter(
            session_id=self.session_id
        ).update(
            is_active=False
        )
    

    @database_sync_to_async
    def check_is_proctor(self):
        if not self.user.is_authenticated:
            return False
        exam = Exam.objects.filter(pk=self.exam_id).first()
        return bool(exam and (
            self.user.pk == exam.company_id
            or (
                self.user.groups.filter(name="Proctor").exists()
                and ProctorEmail.objects.filter(
                    email=self.user.email, submitted_by=exam.company
                ).exists()
            )
        ))

    @database_sync_to_async
    def check_is_student(self):
        return (
            self.user.is_authenticated
            and Exam.objects.filter(pk=self.exam_id, examinees=self.user).exists()
        )
    async def connect(self):

        self.authorized = False

        self.exam_id = self.scope['url_route']['kwargs']['exam_id']

        self.user = self.scope["user"]

        self.proctor_group = (
            f"exam_{self.exam_id}_proctors"
        )

        self.student_group = (
            f"exam_{self.exam_id}_students"
        )

        self.is_proctor = (
            await self.check_is_proctor()
        )

        if not self.is_proctor and not await self.check_is_student():
            await self.close(code=4403)
            return
        self.authorized = True

        if self.is_proctor:

            await self.channel_layer.group_add(
                self.proctor_group,
                self.channel_name
            )

        else:

            self.session_id = (
                f"{self.exam_id}_user_{self.user.id}"
             )

            session = await self.get_or_create_session()

            await self.channel_layer.group_add(
                self.student_group,
                self.channel_name
            )

            await self.channel_layer.group_send(
                self.proctor_group,
                {
                    "type":
                    "student_joined",

                    "masked_session_id":
                    self.session_id[-6:],

                    "full_session_id":
                    self.session_id,

                    "violation_count":
                    session.violation_count,

                    "risk_score":
                    session.risk_score,

                    "event_type":
                    session.latest_event,

                    "is_active":
                    session.is_active,
                }
            )

        await self.accept()

        if self.is_proctor:
            await self.sync_existing_students()


    @database_sync_to_async
    def get_exam_sessions(self):

        return list(
            ExamSession.objects.filter(
            exam_id=self.exam_id
        )
    )

    async def sync_existing_students(self):

        sessions = await self.get_exam_sessions()

        for session in sessions:

            await self.send(
            text_data=json.dumps({

                "type":
                "student_joined",

                "masked_session_id":
                session.session_id[-6:],

                "full_session_id":
                session.session_id,

                "violation_count":
                session.violation_count,

                "risk_score":
                session.risk_score,

                "event_type":
                session.latest_event,
                "is_active":
                session.is_active,
            })
        )
                
    async def disconnect(self, close_code):

        if not getattr(self, "authorized", False):
            return

        if self.is_proctor:

            await self.channel_layer.group_discard(
                self.proctor_group,
                self.channel_name
            )

        else:

            await self.mark_inactive()

            await self.channel_layer.group_send(
                self.proctor_group,
                {
                    "type":
                    "student_status_update",

                    "full_session_id":
                    self.session_id,

                    "is_active":
                    False
                }
            )

            await self.channel_layer.group_discard(
                self.student_group,
                self.channel_name
            )
    async def receive(self, text_data):

        if self.is_proctor:
            return

        data = json.loads(text_data)

        if data.get("type") == "violation":

            event_type = data.get("event")
            if event_type not in VIOLATION_WEIGHTS:
                await self.send(text_data=json.dumps({"type": "error", "error": "invalid_event"}))
                return
            evidence = data.get(
                "evidence"
            )
            print(
                "[EVIDENCE RECEIVED]",
                evidence is not None,
                len(evidence) if evidence else 0
            )

            severity = VIOLATION_WEIGHTS.get(
                event_type,
                5
            )

            session = await self.get_or_create_session()

            session, log = await self.record_violation(
                session=session,
                event_type=event_type,
                severity=severity,
                evidence_image=evidence,
            )

            await self.channel_layer.group_send(
                self.proctor_group,
                {
                    "type":
                    "violation_update",

                    "masked_session_id":
                    self.session_id[-6:],

                    "full_session_id":
                    self.session_id,

                    "violation_count":
                    session.violation_count,

                    "risk_score":
                    session.risk_score,

                    "event_type":
                    event_type,
                    "audit_id":
                    log.id,

                    "evidence_url":
                        (
                    log.evidence_image.url
                    if log.evidence_image
                    else None
                        ),
                    "log_timestamp":
                    log.timestamp.strftime(
                    "%H:%M:%S"
                    )

                }
            )

    async def student_joined(self, event):

        if not self.is_proctor:
            return

        await self.send(
            text_data=json.dumps({

                "type":
                "student_joined",

                "masked_session_id":
                event["masked_session_id"],

                "full_session_id":
                event["full_session_id"],

                "violation_count":
                event["violation_count"],

                "risk_score":
                event["risk_score"],

                "event_type":
                event.get(
                    "event_type",
                    "CONNECTED"
                ),
                "is_active":
                event.get(
                    "is_active",
                    False
                )
            })
        )

    async def violation_update(self, event):

        if not self.is_proctor:
            return

        await self.send(
            text_data=json.dumps({

                "type":
                "violation_update",

                "masked_session_id":
                event["masked_session_id"],

                "full_session_id":
                event["full_session_id"],

                "violation_count":
                event["violation_count"],

                "risk_score":
                event["risk_score"],

                "event_type":
                event["event_type"],
                "audit_id":
                event.get(
                    "audit_id"
                ),

                "evidence_url":
                event.get(
                    "evidence_url"
                ),
                "log_timestamp":
                event.get(
                    "log_timestamp"
                )
            })
        )

    async def student_status_update(self, event):

        if not self.is_proctor:
            return

        await self.send(
            text_data=json.dumps({
                "type":
                "student_status_update",

                "full_session_id":
                event["full_session_id"],

                "is_active":
                event["is_active"]
            })
        )
