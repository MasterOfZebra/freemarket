"""
WebSocket endpoints for real-time chat functionality.

Provides WebSocket connections for exchange chats with Redis Pub/Sub broadcasting.
"""
import json
import logging
from typing import Dict, Any, Optional
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.chat_service import get_chat_service
from backend.models import MessageType
from backend.auth import get_current_user_optional  # JWT validation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Global connection manager for WebSocket connections
class ConnectionManager:
    """Manage active WebSocket connections per exchange"""

    def __init__(self):
        self.active_connections: Dict[str, Dict[int, WebSocket]] = {}  # exchange_id -> {user_id: websocket}

    async def connect(self, exchange_id: str, user_id: int, websocket: WebSocket):
        """Connect user to exchange chat"""
        await websocket.accept()

        if exchange_id not in self.active_connections:
            self.active_connections[exchange_id] = {}

        self.active_connections[exchange_id][user_id] = websocket
        logger.info(f"User {user_id} connected to exchange {exchange_id}")

    def disconnect(self, exchange_id: str, user_id: int):
        """Disconnect user from exchange chat"""
        if exchange_id in self.active_connections:
            if user_id in self.active_connections[exchange_id]:
                del self.active_connections[exchange_id][user_id]

                if not self.active_connections[exchange_id]:
                    del self.active_connections[exchange_id]

                logger.info(f"User {user_id} disconnected from exchange {exchange_id}")

    async def broadcast_to_exchange(self, exchange_id: str, message: Dict[str, Any], exclude_user: Optional[int] = None):
        """Broadcast message to all participants in exchange (except sender)"""
        if exchange_id not in self.active_connections:
            return

        disconnected_users = []

        for user_id, websocket in self.active_connections[exchange_id].items():
            if user_id == exclude_user:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to user {user_id}: {e}")
                disconnected_users.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(exchange_id, user_id)

    def get_exchange_participants(self, exchange_id: str) -> list:
        """Get list of connected users for exchange"""
        if exchange_id in self.active_connections:
            return list(self.active_connections[exchange_id].keys())
        return []


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/exchange/{exchange_id}")
async def exchange_chat(
    websocket: WebSocket,
    exchange_id: str,
    token: str = Query(..., description="JWT access token"),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time exchange chat.

    URL: /ws/chat/exchange/{exchange_id}?token=...

    Message format:
    {
        "type": "message",
        "text": "Hello world!",
        "message_type": "text"
    }
    """
    user = None
    chat_service = get_chat_service(db)

    try:
        # Authenticate user via JWT token
        try:
            from backend.auth import get_current_user
            user = await get_current_user(token)  # This needs to be adapted for WebSocket
        except Exception as e:
            logger.warning(f"WebSocket auth failed: {e}")
            await websocket.close(code=4001, reason="Authentication failed")
            return

        user_id = user.id

        # Validate exchange participation
        if not chat_service.validate_exchange_participant(exchange_id, user_id):
            logger.warning(f"Unauthorized WebSocket connection: user {user_id} for exchange {exchange_id}")
            await websocket.close(code=4003, reason="Not authorized for this exchange")
            return

        # Connect to chat
        await manager.connect(exchange_id, user_id, websocket)

        # Send welcome message and chat history
        try:
            # Send recent chat history
            history = chat_service.get_chat_history(exchange_id, user_id, limit=20)
            if history:
                await websocket.send_json({
                    "type": "history",
                    "messages": history
                })

            # Send online participants
            participants = manager.get_exchange_participants(exchange_id)
            await websocket.send_json({
                "type": "participants_online",
                "participants": participants
            })

        except Exception as e:
            logger.error(f"Failed to send initial data: {e}")

        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()

                message_type = data.get("type", "message")

                if message_type == "message":
                    # Handle chat message
                    message_text = data.get("text", "").strip()
                    msg_type = data.get("message_type", "text")

                    if not message_text:
                        continue

                    # Validate message type
                    try:
                        msg_type_enum = MessageType(msg_type)
                    except ValueError:
                        msg_type_enum = MessageType.TEXT

                    # Save message to database
                    saved_message = chat_service.save_message(
                        exchange_id=exchange_id,
                        sender_id=user_id,
                        message_text=message_text,
                        message_type=msg_type_enum
                    )

                    if saved_message:
                        # Prepare message for broadcasting
                        message_data = {
                            "type": "message",
                            "id": saved_message.id,
                            "exchange_id": exchange_id,
                            "sender_id": user_id,
                            "sender_name": user.full_name or "Unknown",
                            "message_text": message_text,
                            "message_type": msg_type,
                            "created_at": saved_message.created_at.isoformat() if saved_message.created_at else None
                        }

                        # Broadcast to all participants except sender
                        await manager.broadcast_to_exchange(exchange_id, message_data, exclude_user=user_id)

                        # Also broadcast via Redis Pub/Sub for other server instances
                        chat_service.broadcast_message(exchange_id, message_data)

                    else:
                        # Send error to sender
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to send message"
                        })

                elif message_type == "typing_start":
                    # Handle typing indicator start
                    typing_data = {
                        "type": "typing_start",
                        "user_id": user_id,
                        "user_name": user.full_name or "Unknown"
                    }
                    await manager.broadcast_to_exchange(exchange_id, typing_data, exclude_user=user_id)

                elif message_type == "typing_stop":
                    # Handle typing indicator stop
                    typing_data = {
                        "type": "typing_stop",
                        "user_id": user_id
                    }
                    await manager.broadcast_to_exchange(exchange_id, typing_data, exclude_user=user_id)

                elif message_type == "mark_read":
                    # Mark exchange as read for user
                    chat_service.mark_exchange_read(exchange_id, user_id)
                    await websocket.send_json({
                        "type": "marked_read",
                        "exchange_id": exchange_id
                    })

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for user {user_id} in exchange {exchange_id}")
                break

            except Exception as e:
                logger.error(f"WebSocket error for user {user_id}: {e}")
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Internal server error"
                    })
                except:
                    pass
                break

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")

    finally:
        # Always disconnect
        if user:
            manager.disconnect(exchange_id, user.id)


@router.get("/exchanges/{exchange_id}/messages")
def get_chat_messages(
    exchange_id: str,
    current_user = Depends(get_current_user_optional),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get chat message history for an exchange.

    Requires user to be a participant in the exchange.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    chat_service = get_chat_service(db)

    if not chat_service.validate_exchange_participant(exchange_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized for this exchange")

    messages = chat_service.get_chat_history(exchange_id, current_user.id, limit=limit, offset=offset)

    return {
        "exchange_id": exchange_id,
        "messages": messages,
        "limit": limit,
        "offset": offset
    }


@router.get("/unread-counts")
def get_unread_message_counts(
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get unread message counts for all user's exchanges.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    chat_service = get_chat_service(db)
    unread_counts = chat_service.get_unread_count(current_user.id)

    return {
        "unread_counts": unread_counts,
        "total_unread": sum(unread_counts.values())
    }


@router.post("/exchanges/{exchange_id}/messages")
def send_chat_message(
    exchange_id: str,
    message: Dict[str, Any],
    current_user = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Send a message to exchange chat (alternative to WebSocket).

    Mainly for testing or fallback purposes.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    chat_service = get_chat_service(db)

    if not chat_service.validate_exchange_participant(exchange_id, current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized for this exchange")

    message_text = message.get("text", "").strip()
    message_type = message.get("message_type", "text")

    if not message_text:
        raise HTTPException(status_code=400, detail="Message text is required")

    try:
        msg_type_enum = MessageType(message_type)
    except ValueError:
        msg_type_enum = MessageType.TEXT

    saved_message = chat_service.save_message(
        exchange_id=exchange_id,
        sender_id=current_user.id,
        message_text=message_text,
        message_type=msg_type_enum
    )

    if not saved_message:
        raise HTTPException(status_code=500, detail="Failed to save message")

    # Broadcast via Redis
    chat_service.broadcast_message(exchange_id, saved_message.to_dict())

    return {
        "status": "sent",
        "message": saved_message.to_dict()
    }
