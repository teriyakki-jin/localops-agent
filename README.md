# localops-agent

> 내 PC 안에서 돌아가는 업무 OS

로컬-퍼스트 데이터, MCP 툴 연결, 승인 기반 실행을 갖춘 AI 에이전트.

## 아키텍처

```
[CLI / Web UI]
     │
     ▼
[Agent Orchestrator]  ← OpenAI Agents SDK
  ├─ Planner
  ├─ Policy Engine (승인/권한)
  └─ Trace Logger (SQLite)
     │
     ▼
[MCP Servers]  ← FastMCP
  ├─ mcp-fs      (파일 읽기/쓰기)
  ├─ mcp-git     (커밋/diff/브랜치)
  ├─ mcp-notes   (마크다운 노트)
  └─ mcp-runner  (커맨드 샌드박스)
```

## 빠른 시작

```bash
# 1. 의존성 설치
pip install -e ".[dev]"

# 2. 환경 변수 설정
cp .env.example .env
# .env 에 OPENAI_API_KEY 입력

# 3. 실행
python -m agent.orchestrator "지난주 내가 한 일 요약해서 주간보고 만들어줘."
```

## MCP 서버 단독 테스트 (MCP Inspector)

```bash
npx @modelcontextprotocol/inspector python -m mcp_servers.fs_server
```

## 보안 모델

| 권한 | 설명 | 기본 정책 |
|------|------|-----------|
| R | 읽기 | 자동 허용 |
| W | 파일 쓰기 | **승인 필요** |
| X | 커맨드 실행 | **승인 필요** |
| N | 외부 네트워크 | **승인 필요** |

승인 UX: 무엇을 / 왜 / 미리보기(diff) → 이번 한 번 / 세션 동안 / 거부
