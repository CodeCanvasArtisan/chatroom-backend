from fastapi import APIRouter, Depends, HTTPException, status, WebSocket

import json, pytz

from datetime import datetime

from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User, Chat, Message, Membership

import utils.pydantic_models as models

# logger for debugging
from utils.debug_utils import logger

from typing import List, Dict


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket : WebSocket, chat_id : int):
        await websocket.accept()
        
        # Create list for this chat_id if it doesn't exist
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []

        self.active_connections[chat_id].append(websocket)
        print(f"Client connected to chat {chat_id}. Total in room: {len(self.active_connections[chat_id])}")
    
    def disconnect(self, websocket : WebSocket, chat_id : int):
        if chat_id in self.active_connections:
            self.active_connections[chat_id].remove(websocket)
            print(f"Client disconnected from chat {chat_id}. Total in room: {len(self.active_connections[chat_id])}")

            # Clean up empty chatrooms
            if len(self.active_connections[chat_id]) == 0:
                del self.active_connections[chat_id]

    async def broadcast(self, message : str, chat_id : int):
        if chat_id in self.active_connections:
            for connection in self.active_connections[chat_id]:
                await connection.send_text(message)

manager = ConnectionManager()

router = APIRouter()

@router.websocket("/ws/{chat_id}/{user_id}")
async def websocket_endpoint(chat_id : int, websocket : WebSocket, user_id : int, db : Session=Depends(get_db)):
    await manager.connect(websocket, chat_id)

    # join event
    join_message = {
        "type": "user_joined",
        "content": f"{user_id} joined the chat",
        "timestamp": datetime.now(tz=pytz.timezone("Australia/Brisbane")).isoformat(),
        "sender": "system"
    }
    await manager.broadcast(json.dumps(join_message), chat_id)


    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from user {user_id} in chat {chat_id}: {data}")

            # broadcast to all connected clients
            message = {
                "type" : "message",
                "sender" : user_id,
                "content" : data,
                "timestamp" : datetime.now(tz=pytz.timezone("Australia/Brisbane")).isoformat()
            }

            await manager.broadcast(json.dumps(message), chat_id)

            new_message = Message(
                chat_id = chat_id,
                creator_id = user_id,
                content = data,
                time_sent = datetime.now(tz=pytz.timezone("Australia/Brisbane"))
            )
            db.add(new_message)
            db.commit()
            db.refresh(new_message)

    except Exception as e:
        print(f"Error: {e}")
    finally:
         # Notify everyone that this user left
        leave_message = {
            "type": "user_left",
            "content": f"{user_id} left the chat",
            "timestamp": datetime.now(tz=pytz.timezone("Australia/Brisbane")).isoformat(),
            "sender": "system"
        }
        manager.disconnect(websocket, chat_id)

       
