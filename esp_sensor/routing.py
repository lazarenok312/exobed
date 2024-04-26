from django.urls import path
from .consumers import Consumer

websocket_urlpatterns = [
    path('ws/consumer/', Consumer.as_asgi()),
]