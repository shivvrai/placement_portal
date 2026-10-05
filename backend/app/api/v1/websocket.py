import asyncio
import json
import uuid
from typing import Dict, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError
import redis.asyncio as aioredis

from app.core.config import get_settings
from app.core.logging_config import logger

router = APIRouter(tags=["WebSockets"])
settings = get_settings()

class ConnectionManager:
    def __init__(self):
        # user_id -> list[WebSocket]
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    def register(self, user_id: str, ws: WebSocket):
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(ws)

    def unregister(self, user_id: str, ws: WebSocket):
        if user_id in self.active_connections:
            if ws in self.active_connections[user_id]:
                self.active_connections[user_id].remove(ws)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
    async def send_to_user(self, user_id: str, message: dict):
        connections = self.active_connections.get(user_id, [])
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass # Connection might have died unexpectedly

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def ws_endpoint(user_id: str, websocket: WebSocket, token: str = Query(None)):
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("sub") != user_id:
            await websocket.close(code=4003, reason="Token mismatch")
            return
    except JWTError:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()
    manager.register(user_id, websocket)
    
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    channel = f"notif:{user_id}"
    
    async def redis_listener():
        try:
            await pubsub.subscribe(channel)
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    data = json.loads(message['data'])
                    await manager.send_to_user(user_id, data)
        except aioredis.ConnectionError:
            logger.warning("Redis disconnected for WS", user_id=user_id)
        except Exception:
            pass

    async def keepalive():
        try:
            while True:
                await asyncio.sleep(25)
                await manager.send_to_user(user_id, {"type": "ping"})
        except Exception:
            pass
            
    r_task = asyncio.create_task(redis_listener())
    k_task = asyncio.create_task(keepalive())
    
    try:
        while True:
            # We don't expect incoming messages from client for this sprint
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.unregister(user_id, websocket)
        r_task.cancel()
        k_task.cancel()
        try:
            await pubsub.unsubscribe(channel)
        except Exception:
            pass
        try:
            await redis_client.aclose()
        except Exception:
            pass

