from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from utils.auth import verify_access_token
from jose import JWTError

import json, pytz

from datetime import datetime

from sqlalchemy.orm import Session
from database.database import get_db
from database.models import User, Chat, Message, Membership

import utils.pydantic_models as models

# logger for debugging
from utils.debug_utils import logger
from utils.auth import get_current_user_id

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

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(
    chat_id : int, 
    websocket : WebSocket, 
    token : str = Query(...),  # query(...) means this parameter is required (?token=xyz expected)
    db : Session=Depends(get_db)
    ):

    # verify token
    try:
        payload = verify_access_token(token)
        user_id = payload.get("user_id")

        if user_id is None:
            await websocket.close(code=4001, reason="Invalid token")
            return
    
    except Exception as e:
        # Token is invalid/expired
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # after that, accept connection
    await manager.connect(websocket, chat_id)

    # verify that the user is a member of this chat
    membership = db.query(Membership).filter_by(
        chat_id = chat_id,
        user_id = user_id
    ).first()

    if not membership:
        await websocket.close(code=4003, reason="Not a member of this chat")
        manager.disconnect(websocket, chat_id)
        return
    
    # get username for better messages
    user = db.query(User).filter_by(id = user_id).first()
    username = user.username if user else f"User {user_id}"


    # join event
    join_message = {
        "type": "user_joined",
        "content": f"{username} joined the chat",
        "timestamp": datetime.now(tz=pytz.timezone("Australia/Brisbane")).isoformat(),
        "sender": "system"
    }
    await manager.broadcast(json.dumps(join_message), chat_id)


    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from user {username} in chat {chat_id}: {data}")

            # broadcast to all connected clients
            message = {
                "type" : "message",
                "sender" : username,
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

    except WebSocketDisconnect:
        print(f"{username} disconnected from chat {chat_id}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
         # Notify everyone that this user left
        leave_message = {
            "type": "user_left",
            "content": f"{username} left the chat",
            "timestamp": datetime.now(tz=pytz.timezone("Australia/Brisbane")).isoformat(),
            "sender": "system"
        }
        manager.broadcast(json.dumps(leave_message), chat_id)
        manager.disconnect(websocket, chat_id)
