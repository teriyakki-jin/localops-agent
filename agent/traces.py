"""
로컬 트레이스 저장소
- 모든 툴 호출(입력/출력/소요시간/승인여부)을 SQLite에 기록
- "왜 이렇게 했는지" 재현 가능
"""
import json
import time
import asyncio
import aiosqlite
from dataclasses import dataclass, asdict
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "storage" / "traces.db"


@dataclass
class ToolCallTrace:
    session_id: str
    tool_name: str
    arguments: dict
    result: str
    approved: bool
    duration_ms: float
    timestamp: float
    error: str | None = None


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                tool_name TEXT,
                arguments TEXT,
                result TEXT,
                approved INTEGER,
                duration_ms REAL,
                timestamp REAL,
                error TEXT
            )
        """)
        await db.commit()


async def log_tool_call(trace: ToolCallTrace):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO tool_calls
               (session_id, tool_name, arguments, result, approved, duration_ms, timestamp, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trace.session_id,
                trace.tool_name,
                json.dumps(trace.arguments, ensure_ascii=False),
                trace.result[:4000],  # 결과 최대 4000자
                int(trace.approved),
                trace.duration_ms,
                trace.timestamp,
                trace.error,
            ),
        )
        await db.commit()


async def get_session_traces(session_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM tool_calls WHERE session_id = ? ORDER BY timestamp",
            (session_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
