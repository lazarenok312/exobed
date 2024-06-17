import json
from channels.generic.websocket import AsyncWebsocketConsumer


class DeviceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.device_name = self.scope['url_route']['kwargs']['device_name']
        self.room_group_name = f"device_{self.device_name}"

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
        data = json.loads(text_data)
        print(f"Received data from {self.device_name}: {data}")

        await self.send(text_data=json.dumps({
            'message': 'Data received'
        }))
