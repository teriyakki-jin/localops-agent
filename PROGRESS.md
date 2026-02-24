# localops-agent 진행 상황

## 현재 상태 (2026-02-24)

### 완료된 것

| 항목 | 상태 | 비고 |
|------|------|------|
| 프로젝트 폴더 구조 | ✅ | `agent/`, `mcp_servers/`, `configs/`, `storage/` |
| 의존성 설치 | ✅ | `openai-agents`, `fastmcp`, `aiosqlite`, `gitpython` 등 |
| MCP 서버 4개 구현 | ✅ | fs / git / notes / runner |
| MCP 서버 연결 확인 | ✅ | 4개 모두 stdio 연결 성공 |
| OpenAI API 전환 | ✅ | Gemini 제거, `OPENAI_API_KEY` + `gpt-4o` 사용 |
| 에이전트 툴 호출 | ✅ | `git_log`, `list_notes` 등 실제 동작 확인 |
| Windows 한글 콘솔 | ✅ | stdout UTF-8 강제 설정 |
| 429 자동 재시도 | ✅ | 지수 백오프 3회 |
| runner Windows 호환 | ✅ | `ls` → `dir` 자동 변환, async subprocess |
| MCP 연결 타임아웃 튜닝 | ✅ | 5초 → 30초 (`client_session_timeout_seconds`) |
| Git 레포 초기화 | ✅ | 커밋 2개 |
| Policy Engine 연결 | ✅ | `PolicyMCPServer.call_tool()` 오버라이드로 W/X/N 툴 승인 |
| Trace SQLite 로거 연결 | ✅ | 툴 호출마다 traces.db 자동 기록 확인 |
| 승인 UX 동작 확인 | ✅ | 터미널에서 Rich 프롬프트 정상 출력, 1/2/3 선택 동작 |
| 시나리오 1: 주간보고 | ✅ | `git_log` + `list_notes` 수집 → 보고서 초안 생성 → `write_file` 승인 후 저장 |

### 미완료 / 다음 할 것

#### 인프라 보완
- [ ] `mcp-notes` 실제 노트 경로 설정 (`configs/servers.yaml` → `NOTES_PATH` 실제 경로로 변경)
- [ ] MCP Inspector로 각 서버 단독 디버깅
  ```bash
  npx @modelcontextprotocol/inspector python -m mcp_servers.fs_server
  ```

#### 시나리오 2 (다음 단계)
- [ ] `mcp-fs` resource로 PDF/텍스트 읽기 테스트
- [ ] Planner가 2주 일정으로 쪼개는 프롬프트 설계
- [ ] `write_file`로 `README.md`, `SPEC.md`, `TASKS.md` 생성

#### UI (나중에)
- [ ] FastAPI + 브라우저 채팅 UI (로컬 웹)
- [ ] Trace Viewer: 툴 호출 타임라인 표시
- [ ] Task Board: 계획/승인/히스토리

---

## 알려진 이슈

| 이슈 | 원인 | 해결 방법 |
|------|------|-----------|
| `mcp-runner` `ls` 타임아웃 | Windows에 `ls` 없음 | ✅ `dir` 자동 변환으로 수정 완료 |
| FastMCP 배너 stdout 오염 | FastMCP 3.0 stdio 프로토콜 깨짐 | ✅ `show_banner=False` 적용 |
| MCP 서버 초기화 타임아웃 | Windows subprocess 시작 느림 | ✅ `client_session_timeout_seconds=30` 적용 |
| 승인 프롬프트 stdin EOF | Claude Code Bash 툴은 stdin 파이프 | ✅ EOFError 캐치 → 자동 거부 처리, 직접 터미널에서 실행 |
| `mcp-notes` 노트 없음 | `~/notes` 경로 미설정 | `configs/servers.yaml`의 `NOTES_PATH` 실제 경로로 변경 필요 |

---

## 기술 스택

```
에이전트:    OpenAI Agents SDK (Python) + gpt-4o
MCP 서버:   FastMCP 3.0 (stdio transport)
저장소:     SQLite (traces) + 로컬 파일시스템
모델 연결:  OpenAI API (OPENAI_API_KEY, OPENAI_MODEL 환경변수)
```

## 실행 방법

```bash
cd D:\develop\localops-agent

# 기본 실행
python -m agent.orchestrator "질문 또는 작업 내용"

# 예시
python -m agent.orchestrator "이 폴더 구조 간단히 설명해줘"
python -m agent.orchestrator "지난주 내가 한 일 요약해서 주간보고 만들어줘"

# MCP 서버 단독 테스트
npx @modelcontextprotocol/inspector python -m mcp_servers.fs_server
```

## 파일 구조

```
localops-agent/
  agent/
    orchestrator.py   ← 메인 진입점 (PolicyMCPServer + OpenAI gpt-4o)
    policy.py         ← W/X/N 권한 승인 UX (Rich 터미널 프롬프트)
    traces.py         ← SQLite 툴 호출 로거
    evals/
      scenarios.yaml  ← 회귀 테스트 시나리오
  mcp_servers/
    fs_server.py      ← 파일 읽기/쓰기
    git_server.py     ← 커밋/diff/브랜치
    notes_server.py   ← 마크다운 노트
    runner_server.py  ← 커맨드 샌드박스 (async)
  configs/
    policy.yaml       ← 권한 티어 설정
    servers.yaml      ← MCP 서버 allowlist
  storage/
    traces.db         ← 툴 호출 로그 (자동 생성)
  .env                ← API 키 (OPENAI_API_KEY, OPENAI_MODEL)
  pyproject.toml
```
