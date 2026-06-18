import logging

logger = logging.getLogger("devcollab.websocket")


class ConnectionManager:
    def __init__(self):
        self.active: dict[int, list] = {}

    async def connect(self, websocket, project_id: int):
        await websocket.accept()
        if project_id not in self.active:
            self.active[project_id] = []
        self.active[project_id].append(websocket)
        logger.debug(f"WebSocket connected to project {project_id}")

    def disconnect(self, websocket, project_id: int):
        if project_id in self.active:
            self.active[project_id].remove(websocket)
            if not self.active[project_id]:
                del self.active[project_id]

    async def broadcast(self, message: str, project_id: int):
        if project_id not in self.active:
            return

        dead_connections = []
        for connection in self.active[project_id]:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)
                logger.warning(f"Failed to send to a WebSocket in project {project_id}, removing connection")

        # Clean up dead connections
        for dead in dead_connections:
            self.active[project_id].remove(dead)


manager = ConnectionManager()