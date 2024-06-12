from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from channels.auth import AuthMiddlewareStack
from esp_sensor.consumers import DeviceConsumer

application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path("ws/device/<slug:device_name>/", DeviceConsumer.as_asgi()),
        ])
    ),
})