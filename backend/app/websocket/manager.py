import json
from collections import defaultdict
from fastapi import WebSocket
import redis.asyncio as aioredis
from app.config import settings
from app.monitoring.logger import logger


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)
        self._pub_redis: aioredis.Redis | None = None

    async def get_pub_redis(self) -> aioredis.Redis:
        if self._pub_redis is None:
            self._pub_redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._pub_redis

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        self.active_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        if websocket in self.active_connections.get(job_id, []):
            self.active_connections[job_id].remove(websocket)
        if not self.active_connections.get(job_id):
            self.active_connections.pop(job_id, None)

    async def send_progress(self, job_id: str, message: dict):
        # 1. Local delivery (if websocket is connected to this process)
        for ws in list(self.active_connections.get(job_id, [])):
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.debug(f"Direct WS send failed: {e}")

        # 2. Redis Pub/Sub broadcast (for cross-process Celery worker -> FastAPI)
        try:
            r = await self.get_pub_redis()
            await r.publish(f"ws:{job_id}", json.dumps(message))
        except Exception as e:
            logger.debug(f"Redis WS publish failed: {e}")

    async def broadcast(self, message: dict):
        for connections in list(self.active_connections.values()):
            for ws in list(connections):
                try:
                    await ws.send_json(message)
                except Exception:
                    pass
        try:
            r = await self.get_pub_redis()
            await r.publish("ws:broadcast", json.dumps(message))
        except Exception:
            pass


manager = ConnectionManager()
