# localops-agent 진행 상황

## 현재 상태 (2026-02-24)

### 완료된 것

| 항목 | 상태 | 비고 |
|------|------|------|
| 프로젝트 폴더 구조 | ✅ | `agent/`, `mcp_servers/`, `configs/`, `storage/`, `web/` |
| 의존성 설치 | ✅ | `openai-agents`, `fastmcp`, `aiosqlite`, `fastapi`, `uvicorn` 등 |
| MCP 서버 4개 구현 | ✅ | fs / git / notes / runner |
| MCP 서버 연결 확인 | ✅ | 4개 모두 stdio 연결 성공 |
| OpenAI API 전환 | ✅ | `OPENAI_API_KEY` + `gpt-4o` (OPENAI_MODEL 환경변수) |
| MCP 연결 타임아웃 튜닝 | ✅ | 5초 → 30초 (`client_session_timeout_seconds`) |
| Policy Engine 연결 | ✅ | `PolicyMCPServer.call_tool()` 오버라이드로 W/X/N 툴 승인 |
| Trace SQLite 로거 연결 | ✅ | 툴 호출마다 traces.db 자동 기록 확인 |
| 승인 UX (터미널) | ✅ | Rich 프롬프트, 1회/세션/거부 선택, EOFError 처리 |
| Notion MCP 연동 | ✅ | `@notionhq/notion-mcp-server` v2.2.0, NOTION_TOKEN |
| 시나리오 1: 주간보고 | ✅ | git_log + list_notes → 보고서 초안 → write_file 승인 후 저장 |
| Web UI — 채팅 | ✅ | FastAPI + WebSocket, 실시간 메시지, 승인 카드 |
| Web UI — 트레이스 뷰어 | ✅ | 세션 선택, 요약 바, 테이블, 행 클릭 상세 펼치기, 권한/상태 배지 |
| GitHub 연결 | ✅ | https://github.com/teriyakki-jin/localops-agent |

### 미완료 / 다음 할 것

#### 웹 UI
- [ ] 설정 페이지 — 모델 선택, NOTES_PATH 변경, MCP 서버 on/off 토글
- [ ] 트레이스 뷰어 자동 갱신 — 새 세션 생기면 드롭다운 자동 업데이트

#### 인프라
- [ ] `mcp-notes` 실제 노트 경로 설정 (`NOTES_PATH` → Obsidian vault 등)

#### 시나리오 확장
- [ ] 시나리오 2: 파일/문서 읽기 → 스펙 문서 자동 생성
- [ ] Notion에 주간보고 직접 저장 (페이지 ID 고정)

#### UI (나중에)
- [ ] 다크/라이트 테마 전환
- [ ] 모바일 반응형

---

## 실행 방법

```bash
cd D:\develop\localops-agent

# 터미널 CLI
python -m agent.orchestrator "질문 또는 작업 내용"

# 웹 UI
uvicorn web.main:app --reload
# → http://localhost:8000
```

---

## 알려진 이슈

| 이슈 | 원인 | 해결 방법 |
|------|------|-----------|
| 승인 프롬프트 stdin EOF | Claude Code Bash 툴은 stdin 파이프 | ✅ EOFError 자동 거부 처리, 직접 터미널 실행 |
| MCP 서버 초기화 느림 | Windows subprocess 시작 느림 | ✅ timeout 30초로 해결 |
| `mcp-notes` 노트 없음 | `~/notes` 경로 미설정 | `NOTES_PATH` 실제 경로로 변경 필요 |
| 웹 모드 승인 후 세션허용 없음 | 웹 UI는 1회 승인만 지원 | 추후 세션 허용 버튼 추가 예정 |

---

## 기술 스택

```
에이전트:    OpenAI Agents SDK (Python) + gpt-4o
MCP 서버:   FastMCP 3.0 (stdio) — fs / git / notes / runner / notion
웹 서버:    FastAPI + WebSocket + HTMX
저장소:     SQLite (traces) + 로컬 파일시스템
외부 연동:  Notion API (NOTION_TOKEN)
```

## 파일 구조

```
localops-agent/
  agent/
    orchestrator.py   ← 메인 진입점 (PolicyMCPServer + gpt-4o)
    policy.py         ← W/X/N 권한 승인 UX
    traces.py         ← SQLite 툴 호출 로거
  mcp_servers/
    fs_server.py      ← 파일 읽기/쓰기
    git_server.py     ← 커밋/diff/브랜치
    notes_server.py   ← 마크다운 노트
    runner_server.py  ← 커맨드 샌드박스 (async)
  web/
    main.py           ← FastAPI 서버, WebSocket, 트레이스 API
    approval.py       ← asyncio.Event 승인 브리지
    static/
      index.html      ← 채팅 UI + 트레이스 뷰어 + 설정 탭
      style.css
  configs/
    policy.yaml       ← 권한 티어 설정
    servers.yaml      ← MCP 서버 allowlist (notion 포함)
  storage/
    traces.db         ← 툴 호출 로그 (자동 생성)
  .env                ← OPENAI_API_KEY, OPENAI_MODEL, NOTION_TOKEN
```
