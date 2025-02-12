import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from .models import ChatMessage

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

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
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        await sync_to_async(ChatMessage.objects.create)(
            sender=self.scope['user'], 
            message=message
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'timestamp': timezone.now().isoformat(),
                'sender': self.scope['user'].username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender_username = event['sender']

        await self.send(text_data=json.dumps({
            'message': message,
            'timestamp': timezone.now().isoformat(),
            'sender': sender_username
        }))


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
