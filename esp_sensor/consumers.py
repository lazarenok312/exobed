from channels.generic.websocket import AsyncWebsocketConsumer
import json


class ESP8266Consumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sensor_id = self.scope['url_route']['kwargs']['sensor_id']
        self.room_group_name = f'sensor_{self.sensor_id}'
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

    async def sensor_status(self, event):
        blocked = event['blocked']
        # Отправка уведомления о состоянии датчика устройству
        await self.send(text_data=json.dumps({
            'blocked': blocked
        }))
