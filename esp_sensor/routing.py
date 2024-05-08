from django.urls import path
from .consumers import ESP8266Consumer

websocket_urlpatterns = [
    path('ws/sensor/<int:sensor_id>/', ESP8266Consumer.as_asgi()),
]
