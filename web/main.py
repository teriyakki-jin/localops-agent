import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import aiosqlite

from .approval import approval_manager
import os
from agents import RunHooks

class WebHooks(RunHooks):
    async def on_tool_start(self, context, agent, tool):
        await manager.broadcast({
            "type": "tool_start",
            "content": f"[진행 상황] '{tool.name}' 실행 중..."
        })

    async def on_tool_end(self, context, agent, tool, result):
        await manager.broadcast({
            "type": "tool_end",
            "content": f"[완료] '{tool.name}'"
        })

app = FastAPI(title="LocalOps Agent Web UI")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

# Background task to push approval requests to clients
async def stream_approvals():
    while True:
        req = await approval_manager.broadcast_queue.get()
        await manager.broadcast(req)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(stream_approvals())

DB_PATH = Path(__file__).parent.parent / "storage" / "traces.db"

@app.get("/")
async def get_index():
    return FileResponse(static_dir / "index.html")

@app.get("/api/traces/sessions")
async def get_sessions():
    """세션 목록 반환 (최근 20개)."""
    if not DB_PATH.exists():
        return JSONResponse([])
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT session_id, COUNT(*) as tool_count,
                   MIN(timestamp) as started_at, MAX(timestamp) as ended_at
            FROM tool_calls
            GROUP BY session_id
            ORDER BY started_at DESC
            LIMIT 20
        """)
        rows = await cursor.fetchall()
        return JSONResponse([dict(r) for r in rows])

@app.get("/api/traces/{session_id}")
async def get_session_traces(session_id: str):
    """특정 세션의 툴 호출 목록 반환."""
    if not DB_PATH.exists():
        return JSONResponse([])
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT id, tool_name, arguments, result, approved, duration_ms, timestamp, error
            FROM tool_calls WHERE session_id = ? ORDER BY timestamp
        """, (session_id,))
        rows = await cursor.fetchall()
        return JSONResponse([dict(r) for r in rows])

async def run_agent_task(user_msg: str):
    os.environ["LOCALOPS_WEB_MODE"] = "1"
    try:
        from agent.orchestrator import run
        hooks = WebHooks()
        final_output = await run(user_msg, hooks=hooks)
        await manager.broadcast({
            "type": "agent_message",
            "content": final_output
        })
    except Exception as e:
        await manager.broadcast({
            "type": "agent_message",
            "content": f"에러 발생: {str(e)}"
        })

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue
                
            msg_type = payload.get("type")
            
            if msg_type == "chat":
                user_msg = payload.get("message")
                asyncio.create_task(run_agent_task(user_msg))
                
            elif msg_type == "approval_response":
                request_id = payload.get("request_id")
                approved = payload.get("approved")
                if request_id:
                    approval_manager.resolve_approval(request_id, bool(approved))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
