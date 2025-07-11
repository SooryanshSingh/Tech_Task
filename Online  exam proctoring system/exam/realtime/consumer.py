import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone



class ExamControlConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.exam_id = self.scope['url_route']['kwargs']['exam_id']
        self.room_group_name = f'exam_{self.exam_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):

        data = json.loads(text_data)
        print("Received WebSocket message:", data)  # Debugging

        if data.get("type") == "close_exam":  # Ensure correct key is checked
            await self.close_exam()

    async def close_exam(self):
        """Notify all students that the exam is closed."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "exam_closed_message",  # Must match function name below
            }
        )

    async def exam_closed_message(self, event):
        """Send an 'exam_closed' event to all connected students."""
        await self.send(text_data=json.dumps({"type": "exam_closed"}))




class TabMonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get exam ID from URL route
        self.exam_id = self.scope['url_route']['kwargs']['exam_id']
        self.room_group_name = f'tab_monitor_{self.exam_id}'

        # Join group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Receive message from WebSocket
        data = json.loads(text_data)
        print("Received Tab Change WebSocket message:", data)

        if data.get("type") == "tab_change":
            await self.handle_tab_change(data)

    async def handle_tab_change(self, data):
        # Broadcast tab change event to the group
        sender = data.get("sender", "Unknown")
        message = data.get("message", "Tab change detected")

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "tab_change_message",  #must match a mthod name
                "sender": sender,
                "message": message,
            }
        )

    async def tab_change_message(self, event):
        # Send the tab change message to WebSocket
        await self.send(text_data=json.dumps({
            "type": "tab_change",
            "sender": event.get("sender"),
            "message": event.get("message"),
        }))

import json
from channels.generic.websocket import AsyncWebsocketConsumer

#from asgiref.sync import sync_to_async

import json
from channels.generic.websocket import AsyncWebsocketConsumer

class WebRTCConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['exam_id']
        self.room_group_name = f'webrtc_{self.room_name}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # ✅ Notify all clients (i.e., student) that someone joined (likely proctor)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'proctor_joined',
                'from': 'server'
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'signal_message',
                'message': text_data
            }
        )

    async def signal_message(self, event):
        await self.send(text_data=event['message'])

    # ✅ New: Triggered when a peer joins (used to prompt re-offer)
    async def proctor_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'proctor-joined'
        }))
