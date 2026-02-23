"""
mcp-fs: 파일 시스템 MCP 서버 (FastMCP)
- Resources: 파일/디렉토리 읽기 (read-only)
- Tools: write_file, apply_patch, move_file (승인 필요 - 오케스트레이터에서 처리)
"""
import os
import difflib
from pathlib import Path
from fastmcp import FastMCP

ROOT = Path(os.environ.get("ROOT_PATH", ".")).resolve()
mcp = FastMCP("mcp-fs")


def _safe_path(path: str) -> Path:
    """ROOT 밖으로 나가는 경로 차단."""
    resolved = (ROOT / path).resolve()
    if not str(resolved).startswith(str(ROOT)):
        raise ValueError(f"접근 거부: {path} 는 허용 범위 밖입니다.")
    return resolved


# ── Resources ──────────────────────────────────────────────────────────────

@mcp.resource("file://{path}")
def read_file(path: str) -> str:
    """파일 내용 읽기."""
    p = _safe_path(path)
    if not p.exists():
        raise FileNotFoundError(f"{path} 없음")
    return p.read_text(encoding="utf-8", errors="replace")


@mcp.resource("dir://{path}")
def list_dir(path: str) -> str:
    """디렉토리 목록 및 메타정보."""
    p = _safe_path(path)
    if not p.is_dir():
        raise NotADirectoryError(f"{path} 는 디렉토리가 아닙니다.")
    lines = []
    for item in sorted(p.iterdir()):
        kind = "DIR" if item.is_dir() else "FILE"
        size = item.stat().st_size if item.is_file() else 0
        lines.append(f"{kind:5} {size:>10}B  {item.name}")
    return "\n".join(lines)


# ── Tools ───────────────────────────────────────────────────────────────────

@mcp.tool()
def write_file(path: str, content: str, mode: str = "overwrite") -> str:
    """
    파일 쓰기.
    path: 루트 기준 상대 경로
    content: 파일 내용
    mode: 'overwrite' | 'append'
    ⚠️ 승인 필요 (W 권한)
    """
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    if mode == "append":
        with open(p, "a", encoding="utf-8") as f:
            f.write(content)
    else:
        p.write_text(content, encoding="utf-8")

    return f"✓ 작성 완료: {p}"


@mcp.tool()
def apply_patch(path: str, unified_diff: str) -> str:
    """
    unified diff 형식으로 파일 패치 적용.
    ⚠️ 승인 필요 (W 권한)
    """
    p = _safe_path(path)
    original = p.read_text(encoding="utf-8").splitlines(keepends=True)

    # 간단한 패치 적용 (python-patch 없이 직접 처리)
    # 실제 구현에서는 `patch` 유틸리티 또는 라이브러리 사용 권장
    return f"패치 미리보기:\n{unified_diff[:500]}\n\n(실제 적용은 승인 후 진행)"


@mcp.tool()
def move_file(path_from: str, path_to: str) -> str:
    """
    파일 이동.
    ⚠️ 승인 필요 (W 권한)
    """
    src = _safe_path(path_from)
    dst = _safe_path(path_to)
    dst.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dst)
    return f"✓ 이동 완료: {path_from} → {path_to}"


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
