"""
Standalone WebSocket Gateway for scaling.

This service handles WebSocket connections independently of API instances.
"""
import os
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware

# Import our WebSocket chat handler
from .api.endpoints.chat import ConnectionManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FreeMarket WebSocket Gateway",
    version="1.0.0",
    description="WebSocket gateway for real-time chat functionality"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global connection manager
manager = ConnectionManager()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "websocket-gateway"}

@app.websocket("/ws/chat/exchange/{exchange_id}")
async def exchange_chat_gateway(
    websocket: WebSocket,
    exchange_id: str,
    token: str = None
):
    """
    WebSocket endpoint for exchange chat (gateway version).

    This is a simplified version that delegates to the main chat handler.
    In production, this would include proper authentication and scaling.
    """
    # For now, accept all connections (add authentication in production)
    await websocket.accept()

    # Generate a temporary user ID (replace with real auth)
    user_id = hash(token or "anonymous") % 10000  # Temporary

    logger.info(f"Gateway: User {user_id} connecting to exchange {exchange_id}")

    # Connect to exchange
    await manager.connect(exchange_id, user_id, websocket)

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            message_type = data.get("type", "message")

            if message_type == "message":
                # Broadcast message to all participants
                await manager.broadcast_to_exchange(
                    exchange_id,
                    {
                        "type": "message",
                        "sender_id": user_id,
                        "message_text": data.get("text", ""),
                        "message_type": data.get("message_type", "text"),
                        "created_at": "2025-01-01T00:00:00Z"  # Placeholder
                    },
                    exclude_user=None  # Broadcast to all
                )

            elif message_type == "typing_start":
                await manager.broadcast_to_exchange(
                    exchange_id,
                    {
                        "type": "typing_start",
                        "user_id": user_id
                    },
                    exclude_user=user_id
                )

            elif message_type == "typing_stop":
                await manager.broadcast_to_exchange(
                    exchange_id,
                    {
                        "type": "typing_stop",
                        "user_id": user_id
                    },
                    exclude_user=user_id
                )

    except WebSocketDisconnect:
        logger.info(f"Gateway: User {user_id} disconnected from exchange {exchange_id}")
    except Exception as e:
        logger.error(f"Gateway error for user {user_id}: {e}")
    finally:
        manager.disconnect(exchange_id, user_id)

@app.get("/stats")
def get_connection_stats():
    """Get WebSocket connection statistics"""
    total_connections = sum(len(connections) for connections in manager.active_connections.values())

    return {
        "active_exchanges": len(manager.active_connections),
        "total_connections": total_connections,
        "exchanges": list(manager.active_connections.keys())
    }

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("WS_HOST", "0.0.0.0")
    port = int(os.getenv("WS_PORT", "8080"))

    logger.info(f"Starting WebSocket Gateway on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
