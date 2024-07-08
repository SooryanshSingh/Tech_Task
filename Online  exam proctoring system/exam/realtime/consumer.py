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
import json
from channels.generic.websocket import AsyncWebsocketConsumer
class RTCConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'rtc_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"WebSocket connection established for room {self.room_name}")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f"WebSocket connection closed for room {self.room_name} with code {close_code}")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        print(f"Received WebSocket data: {text_data}")

        if message_type == 'offer' or message_type == 'answer' or message_type == 'candidate':
            print(f"Processing {message_type} message")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'rtc.message',
                    'message': text_data,
                }
            )
        else:
            print(f"Ignoring unknown message type: {message_type}")

    async def rtc_message(self, event):
        message = event['message']
        print(f"Sending RTC message: {message}")
        await self.send(text_data=message)
