import asyncio
import uuid
from typing import Any

class ApprovalManager:
    def __init__(self):
        self.pending_requests: dict[str, dict] = {}
        self.broadcast_queue = asyncio.Queue()

    async def request_approval_async(self, tool_name: str, arguments: dict, reason: str = "") -> bool:
        """웹 UI에 승인 요청을 보내고 응답을 대기 (비동기)"""
        request_id = str(uuid.uuid4())
        event = asyncio.Event()
        self.pending_requests[request_id] = {
            "event": event,
            "approved": False
        }
        
        # WebSocket 브로드캐스트용 큐에 요청 넣기
        await self.broadcast_queue.put({
            "type": "approval_request",
            "request_id": request_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "reason": reason
        })
        
        # UI 응답 대기
        await event.wait()
        
        result = self.pending_requests[request_id]["approved"]
        del self.pending_requests[request_id]
        return result

    def resolve_approval(self, request_id: str, approved: bool):
        """웹 UI로부터 승인/거부 응답을 받아 이벤트를 해제"""
        if request_id in self.pending_requests:
            self.pending_requests[request_id]["approved"] = approved
            self.pending_requests[request_id]["event"].set()

approval_manager = ApprovalManager()
