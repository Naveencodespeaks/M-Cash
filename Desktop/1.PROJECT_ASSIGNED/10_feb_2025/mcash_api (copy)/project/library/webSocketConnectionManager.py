from fastapi import WebSocket
import json

class WebSocketConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        try:
            await websocket.accept()
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            self.active_connections[user_id] = websocket
        except Exception as E:
            print(E)      
    

    def disconnect(self, user_id: int):
        try:
            print(f''' disconneced : {user_id}''')
            del self.active_connections[user_id]
        except Exception as E:
            print(E)      

    async def send_message(self, user_id: int, message=''):
        websocket = self.active_connections.get(user_id)
        if websocket:
            if isinstance(message, dict):
                message = json.dumps(message)
            try:
                await websocket.send_text(message)
            except Exception as e:
                print(f"Error sending message to {user_id}: {e}")
                self.disconnect(user_id)  # Cleanup on error
    
    async def send_message_to_multiple(self, user_ids=[], message=''):
        try:
            if isinstance(message, dict):
                message = json.dumps(message)  # Convert dict to JSON string
            
            for user_id in user_ids:
                websocket = self.active_connections.get(user_id)
                if websocket:
                    await websocket.send_text(message)
        except Exception as E:
            print(E)            

# Create a global instance of ConnectionManager
manager = WebSocketConnectionManager()
