import json
from collections import defaultdict

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from .models import ExamAuditLog


EXAM_SESSIONS = defaultdict(dict)

VIOLATION_WEIGHTS = {
    "TAB_SWITCH": 10,
    "FULLSCREEN_EXIT": 15,
    "NO_FACE": 20,
    "MULTIPLE_FACES": 35,
}


class ExamControlConsumer(AsyncWebsocketConsumer):

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
        self.exam_id = self.scope['url_route']['kwargs']['exam_id']

        self.room_group_name = f'exam_{self.exam_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):

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
    def load_session_state(self):

        logs = ExamAuditLog.objects.filter(
            exam_id=self.exam_id,
            session_id=self.session_id
        ).order_by("timestamp")

        violation_count = logs.count()

        risk_score = sum(
            log.severity
            for log in logs
        )

        latest_event = (
            logs.last().event_type
            if logs.exists()
            else "CONNECTED"
        )

        events = []

        for log in logs:

            events.append({
                "event": log.event_type
            })

        return {

            "violation_count":
            violation_count,

            "risk_score":
            risk_score,

            "latest_event":
            latest_event,

            "events":
            events
        }

    @database_sync_to_async
    def log_event(
        self,
        event_type,
        severity,
        metadata=None
    ):
        ExamAuditLog.objects.create(
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

    @database_sync_to_async
    def check_is_proctor(self):

        return (
            self.user.is_authenticated
            and
            self.user.groups.filter(
                name="Proctor"
            ).exists()
        )

    async def connect(self):

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

        if self.is_proctor:

            await self.channel_layer.group_add(
                self.proctor_group,
                self.channel_name
            )

        else:

            self.session_id = (
                f"{self.exam_id}_user_{self.user.id}"
            )

            if self.session_id not in EXAM_SESSIONS[self.exam_id]:

                EXAM_SESSIONS[
                    self.exam_id
                ][self.session_id] = (
                    await self.load_session_state()
                )

            session = EXAM_SESSIONS[
                self.exam_id
            ][self.session_id]

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
                    session["violation_count"],

                    "risk_score":
                    session["risk_score"],

                    "event_type":
                    session["latest_event"],
                }
            )

        await self.accept()

        if self.is_proctor:
            await self.sync_existing_students()

    async def sync_existing_students(self):

        sessions = EXAM_SESSIONS.get(
            self.exam_id,
            {}
        )

        for session_id, data in sessions.items():

            await self.send(
                text_data=json.dumps({

                    "type":
                    "student_joined",

                    "masked_session_id":
                    session_id[-6:],

                    "full_session_id":
                    session_id,

                    "violation_count":
                    data["violation_count"],

                    "risk_score":
                    data["risk_score"],

                    "event_type":
                    data.get(
                        "latest_event",
                        "CONNECTED"
                    ),
                })
            )

    async def disconnect(self, close_code):

        if self.is_proctor:

            await self.channel_layer.group_discard(
                self.proctor_group,
                self.channel_name
            )

        else:

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

            severity = VIOLATION_WEIGHTS.get(
                event_type,
                5
            )

            session = EXAM_SESSIONS[
                self.exam_id
            ].get(
                self.session_id
            )

            if not session:
                return

            session["violation_count"] += 1

            session["risk_score"] += severity

            session["latest_event"] = event_type

            session["events"].append({
                "event": event_type
            })

            await self.log_event(
                event_type=event_type,

                severity=severity,

                metadata={
                    "risk_score":
                    session["risk_score"]
                }
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
                    session["violation_count"],

                    "risk_score":
                    session["risk_score"],

                    "event_type":
                    event_type,
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
            })
        )