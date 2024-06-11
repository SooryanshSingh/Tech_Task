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

