from channels.generic.websocket import AsyncWebsocketConsumer


class Consumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        # Обработка полученных данных
        await self.send(text_data)
