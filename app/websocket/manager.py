class ConnectionManager:
    def __init__(self):
        self.active = {}
        self.history = {}

    async def connect(self, websocket, project_id):
        await websocket.accept()
        if project_id not in self.active:
            self.active[project_id] = []
            self.history[project_id] = []
        self.active[project_id].append(websocket)

    def disconnect(self,websocket,project_id):
        self.active[project_id].remove(websocket)

    async def broadcast(self, message, project_id):
        dead=[]
        for connection in self.active[project_id]:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.active[project_id].remove(connection)


manager = ConnectionManager()