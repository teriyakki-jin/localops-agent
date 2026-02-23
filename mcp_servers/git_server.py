"""
mcp-git: Git MCP 서버 (FastMCP)
- Resources: log, diff, status (read-only)
- Tools: create_branch, git_commit, open_pr (승인 필요)
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
import git
from fastmcp import FastMCP

REPO_PATH = Path(os.environ.get("REPO_PATH", ".")).resolve()
mcp = FastMCP("mcp-git")


def _repo() -> git.Repo:
    return git.Repo(REPO_PATH, search_parent_directories=True)


# ── Tools (읽기 전용 쿼리 - 파라미터가 있어 tool로 선언) ─────────────────────

@mcp.tool()
def git_log(since_days: int = 7, max_count: int = 50) -> str:
    """
    최근 커밋 로그.
    since_days: 며칠 전부터 (기본 7일)
    max_count: 최대 커밋 수
    """
    repo = _repo()
    since = datetime.now() - timedelta(days=since_days)
    lines = []
    for commit in repo.iter_commits(since=since.isoformat(), max_count=max_count):
        lines.append(
            f"{commit.hexsha[:8]} | {commit.committed_datetime.strftime('%Y-%m-%d %H:%M')} "
            f"| {commit.author.name} | {commit.message.strip()[:80]}"
        )
    return "\n".join(lines) if lines else "(커밋 없음)"


@mcp.tool()
def git_diff(base: str = "HEAD~7", head: str = "HEAD") -> str:
    """두 커밋 간 변경 내역 요약 (--stat)."""
    repo = _repo()
    try:
        diff = repo.git.diff("--stat", base, head)
        return diff or "(변경 없음)"
    except git.GitCommandError as e:
        return f"diff 오류: {e}"


@mcp.tool()
def git_status() -> str:
    """현재 작업 트리 상태."""
    repo = _repo()
    status = repo.git.status("--short")
    return status or "(깨끗한 상태)"


@mcp.tool()
def git_branches() -> str:
    """브랜치 목록."""
    repo = _repo()
    branches = [b.name for b in repo.branches]
    current = repo.active_branch.name
    return "\n".join(f"{'*' if b == current else ' '} {b}" for b in branches)


# ── Tools ───────────────────────────────────────────────────────────────────

@mcp.tool()
def create_branch(name: str) -> str:
    """
    새 브랜치 생성.
    ⚠️ 승인 필요 (W 권한)
    """
    repo = _repo()
    repo.git.checkout("-b", name)
    return f"✓ 브랜치 생성: {name}"


@mcp.tool()
def git_commit(message: str, files: list[str] | None = None) -> str:
    """
    스테이징 후 커밋.
    files: 커밋할 파일 목록 (None이면 수동 스테이징 필요)
    ⚠️ 승인 필요 (W 권한)
    """
    repo = _repo()
    if files:
        repo.index.add(files)
    commit = repo.index.commit(message)
    return f"✓ 커밋: {commit.hexsha[:8]} - {message}"


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
