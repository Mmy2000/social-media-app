import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ConversationMessage


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        if self.scope["user"].is_authenticated:
            self.user_group_name = f"user_{self.scope['user'].id}"
            await self.channel_layer.group_add(self.user_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        if hasattr(self, "user_group_name"):
            await self.channel_layer.group_discard(
                self.user_group_name, self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event_type = data.get("event")

        if event_type == "chat_message":
            conversation_id = data["data"]["conversation_id"]
            sent_to_id = data["data"]["sent_to_id"]
            name = data["data"]["name"]
            body = data["data"]["body"]

            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat_message", "body": body, "name": name},
            )

            await self.save_message(conversation_id, body, sent_to_id)

            await self.channel_layer.group_send(
                f"user_{sent_to_id}",
                {
                    "type": "new_message_notification",
                    "message": f"New message from {name}",
                    "from_user": name,
                },
            )

        elif event_type == "typing":
            name = data["data"]["name"]
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "user_typing", "name": name}
            )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {"event": "chat_message", "body": event["body"], "name": event["name"]}
            )
        )

    async def user_typing(self, event):
        await self.send(
            text_data=json.dumps({"event": "typing", "name": event["name"]})
        )

    async def new_message_notification(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "event": "new_message_notification",
                    "message": event["message"],
                    "from_user": event["from_user"],
                }
            )
        )

    @sync_to_async
    def save_message(self, conversation_id, body, sent_to_id):
        user = self.scope["user"]
        ConversationMessage.objects.create(
            conversation_id=conversation_id,
            body=body,
            sent_to_id=sent_to_id,
            created_by=user,
        )
