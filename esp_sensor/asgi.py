import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import esp_sensor.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exobed.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            esp_sensor.routing.websocket_urlpatterns
        )
    ),
})
