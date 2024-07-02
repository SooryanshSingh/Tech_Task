# consumer.py
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
        message_type = text_data_json.get('type')

        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'webrtc_offer':
            await self.handle_webrtc_offer(text_data_json)
        elif message_type == 'webrtc_answer':
            await self.handle_webrtc_answer(text_data_json)
        elif message_type == 'webrtc_ice_candidate':
            await self.handle_webrtc_ice_candidate(text_data_json)

    async def handle_chat_message(self, text_data_json):
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

    async def handle_webrtc_offer(self, text_data_json):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_offer',
                'offer': text_data_json['offer'],
                'sender': self.scope['user'].username
            }
        )

    async def handle_webrtc_answer(self, text_data_json):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_answer',
                'answer': text_data_json['answer'],
                'sender': self.scope['user'].username
            }
        )

    async def handle_webrtc_ice_candidate(self, text_data_json):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_ice_candidate',
                'candidate': text_data_json['candidate'],
                'sender': self.scope['user'].username
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender_username = event['sender']
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message,
            'timestamp': timezone.now().isoformat(),
            'sender': sender_username
        }))

    async def webrtc_offer(self, event):
        offer = event['offer']
        sender_username = event['sender']
        await self.send(text_data=json.dumps({
            'type': 'webrtc_offer',
            'offer': offer,
            'sender': sender_username
        }))

    async def webrtc_answer(self, event):
        answer = event['answer']
        sender_username = event['sender']
        await self.send(text_data=json.dumps({
            'type': 'webrtc_answer',
            'answer': answer,
            'sender': sender_username
        }))

    async def webrtc_ice_candidate(self, event):
        candidate = event['candidate']
        sender_username = event['sender']
        await self.send(text_data=json.dumps({
            'type': 'webrtc_ice_candidate',
            'candidate': candidate,
            'sender': sender_username
        }))

