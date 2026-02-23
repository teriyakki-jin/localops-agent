"""
mcp-notes: 마크다운 노트 MCP 서버 (FastMCP)
Obsidian 또는 일반 .md 폴더와 연동
"""
import os
import re
from pathlib import Path
from fastmcp import FastMCP

NOTES_PATH = Path(os.environ.get("NOTES_PATH", "~/notes")).expanduser().resolve()
mcp = FastMCP("mcp-notes")


def _all_notes() -> list[Path]:
    return sorted(NOTES_PATH.rglob("*.md")) if NOTES_PATH.exists() else []


# ── Resources ──────────────────────────────────────────────────────────────

@mcp.resource("note://{note_id}")
def read_note(note_id: str) -> str:
    """노트 읽기. note_id는 파일명(확장자 제외) 또는 상대 경로."""
    for p in _all_notes():
        if p.stem == note_id or p.name == note_id or str(p.relative_to(NOTES_PATH)) == note_id:
            return p.read_text(encoding="utf-8")
    raise FileNotFoundError(f"노트 없음: {note_id}")


@mcp.tool()
def search_notes(q: str, max_results: int = 10) -> str:
    """
    노트 전문 검색.
    q: 검색 키워드 (공백 구분 AND)
    max_results: 최대 결과 수
    """
    keywords = q.lower().split()
    results = []
    for p in _all_notes():
        content = p.read_text(encoding="utf-8", errors="replace").lower()
        if all(k in content for k in keywords):
            for line in content.splitlines():
                if any(k in line for k in keywords):
                    snippet = line.strip()[:100]
                    break
            else:
                snippet = ""
            results.append(f"{p.relative_to(NOTES_PATH)}: {snippet}")
        if len(results) >= max_results:
            break
    return "\n".join(results) if results else "(검색 결과 없음)"


@mcp.tool()
def list_notes(limit: int = 30) -> str:
    """최근 수정된 노트 목록."""
    notes = sorted(_all_notes(), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    return "\n".join(str(p.relative_to(NOTES_PATH)) for p in notes)


# ── Tools ───────────────────────────────────────────────────────────────────

@mcp.tool()
def create_note(title: str, content: str, folder: str = "") -> str:
    """
    새 노트 생성.
    ⚠️ 승인 필요 (W 권한)
    """
    safe_title = re.sub(r'[\\/*?:"<>|]', "-", title)
    base = NOTES_PATH / folder if folder else NOTES_PATH
    base.mkdir(parents=True, exist_ok=True)
    p = base / f"{safe_title}.md"
    p.write_text(content, encoding="utf-8")
    return f"✓ 노트 생성: {p.relative_to(NOTES_PATH)}"


@mcp.tool()
def append_note(note_id: str, content: str) -> str:
    """
    기존 노트에 내용 추가.
    ⚠️ 승인 필요 (W 권한)
    """
    for p in _all_notes():
        if p.stem == note_id or p.name == note_id:
            with open(p, "a", encoding="utf-8") as f:
                f.write("\n" + content)
            return f"✓ 추가 완료: {p.relative_to(NOTES_PATH)}"
    raise FileNotFoundError(f"노트 없음: {note_id}")


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
