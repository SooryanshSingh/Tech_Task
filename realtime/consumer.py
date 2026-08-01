import json
from collections import defaultdict

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.db import transaction
from django.db.models import F
from Home.models import Exam, ProctorEmail

from .models import (
    ExamAuditLog,
    ExamSession
)
import base64
import uuid

from django.core.files.base import ContentFile


VIOLATION_WEIGHTS = {
    "TAB_SWITCH": 10,
    "FULLSCREEN_EXIT": 15,
    "NO_FACE": 20,
    "MULTIPLE_FACES": 35,
    "PHONE_DETECTED": 40,

}
MAX_EVIDENCE_SIZE = 500_000

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

            await self.log_event(
                event_type="EXAM_CLOSED",
                severity=100,
                metadata={
                    "exam_id": self.exam_id
                }
            )

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type":
                    "exam_closed"
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
                "exam_closed"
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
    
    @database_sync_to_async
    def log_event(
    self,
    event_type,
    severity,
    metadata=None,
    evidence_image=None):

        log = ExamAuditLog.objects.create(
        exam_id=self.exam_id,

        actor=(
            self.user
            if self.user.is_authenticated
            else None
        ),

        session_id=self.session_id,

        event_type=event_type,

        severity=severity,

        metadata=metadata or {}
    )

        if evidence_image:

            try:
                if event_type not in ALLOWED_EVIDENCE_EVENTS:

                    evidence_image = None
                if evidence_image:

                    if len(evidence_image) > MAX_EVIDENCE_SIZE:

                        print("[EVIDENCE] Too large")

                        evidence_image = None

                    if evidence_image:

                        header, imgstr = evidence_image.split(
                    ";base64,"
                    )

                        file = ContentFile(
                        base64.b64decode(imgstr),
                        name=f"{uuid.uuid4()}.jpg"
                    )

                        log.evidence_image.save(
                        file.name,
                        file,
                        save=True
                    )
            except Exception as e:

                print(
                "[EVIDENCE SAVE ERROR]",
                e
            )

        return log
    
    @database_sync_to_async
    def update_session(
        self,
        session,
        severity,
        event_type
        ):

        with transaction.atomic():
            ExamSession.objects.filter(pk=session.pk).update(
                violation_count=F("violation_count") + 1,
                risk_score=F("risk_score") + severity,
                latest_event=event_type,
            )
            return ExamSession.objects.get(pk=session.pk)
    
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
    @database_sync_to_async
    def evidence_count(self):

        return ExamAuditLog.objects.filter(
        session_id=self.session_id
    ).exclude(evidence_image__isnull=True).count()

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

            session = await self.update_session(session,severity,event_type)            
            
            
            
            evidence_count = (
                await self.evidence_count()
            )

            if (
                evidence_count >=
                MAX_EVIDENCE_PER_SESSION
            ):
                evidence = None
            log = await self.log_event(
                event_type=event_type,

                severity=severity,

                metadata={
                    "risk_score":
                    session.risk_score
                },
                evidence_image = evidence
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
