import json
from channels.generic.websocket import AsyncWebsocketConsumer

# This creates a global memory "set" to track who is currently connected
connected_users = set()

class OnlineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.group_name = "online_users"

        if self.user.is_anonymous:
            await self.close()
        else:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            
            # Add the user to our memory set
            connected_users.add(self.user.username)

            # Broadcast the full list to everyone!
            await self.broadcast_online_users()

    async def disconnect(self, close_code):
        # Remove them when they log out or close the tab
        if self.user.username in connected_users:
            connected_users.remove(self.user.username)
            
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        
        # Broadcast the updated list so they disappear from everyone's screen
        await self.broadcast_online_users()

    async def broadcast_online_users(self):
        # Sends the current list of users to our handler function below
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "user_status_update",
                "users": list(connected_users)
            }
        )

    async def user_status_update(self, event):
        users = event["users"]
        
        # ROLE-BASED LOGIC: Superadmins, HR, and Staff see the names. Others see the count.
        if self.user.is_staff or self.user.is_superuser or getattr(self.user, 'is_hr', False):
            # Formats the names into a clean HTML list
            details = f"<strong>{len(users)} Online:</strong><br>" + "<br>".join(f"🟢 {u}" for u in users)
        else:
            details = f"<strong>{len(users)}</strong> users currently online."

        await self.send(text_data=json.dumps({
            "status": "update",
            "details": details
        }))