from django.urls import path, re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from realtime.consumer import  ExamControlConsumer ,WebRTCConsumer, TabMonitorConsumer

websocket_urlpatterns = [
    path('ws/exam/<int:exam_id>/', ExamControlConsumer.as_asgi()), 
    path('ws/stream/<int:exam_id>/', WebRTCConsumer.as_asgi()), 
    path('ws/exam/tab/<int:exam_id>/', TabMonitorConsumer.as_asgi())
]
application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
    
})

