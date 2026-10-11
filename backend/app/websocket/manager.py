from collections import defaultdict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, job_id: str):
        await websocket.accept()
        self.active_connections[job_id].append(websocket)

    def disconnect(self, websocket: WebSocket, job_id: str):
        self.active_connections[job_id].remove(websocket)
        if not self.active_connections[job_id]:
            del self.active_connections[job_id]

    async def send_progress(self, job_id: str, message: dict):
        for ws in self.active_connections.get(job_id, []):
            await ws.send_json(message)

    async def broadcast(self, message: dict):
        for connections in self.active_connections.values():
            for ws in connections:
                await ws.send_json(message)


manager = ConnectionManager()
