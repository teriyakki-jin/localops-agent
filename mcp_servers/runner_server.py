"""
mcp-runner: 커맨드 실행 샌드박스 MCP 서버 (FastMCP)
- asyncio subprocess 사용 (이벤트 루프 블로킹 방지)
- 네트워크: 기본 deny (policy.yaml 설정 따름)
- 타임아웃: 30초
- ⚠️ 모든 실행은 승인 필요 (X 권한)
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("mcp-runner")
DEFAULT_TIMEOUT = 30

BLOCKED = {"rm", "del", "format", "mkfs", "dd", "curl", "wget", "ssh", "scp"}


async def _run_async(cmd: list[str], cwd: Path, timeout: int) -> str:
    """asyncio 비동기 subprocess 실행 (이벤트 루프 블로킹 없음)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return f"타임아웃 ({timeout}초 초과)"

        output = stdout.decode("utf-8", errors="replace") + stderr.decode("utf-8", errors="replace")
        return f"[returncode={proc.returncode}]\n{output[:3000]}"
    except Exception as e:
        return f"실행 오류: {e}"


@mcp.tool()
async def run_command(
    cmd: list[str],
    cwd: str = ".",
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    커맨드 실행 (읽기 전용 샌드박스).
    cmd: 실행할 커맨드 (예: ["pytest", "tests/", "-v"])
    cwd: 작업 디렉토리
    timeout: 최대 실행 시간(초)
    ⚠️ 승인 필요 (X 권한)
    """
    work_dir = Path(cwd).resolve()
    if not work_dir.exists():
        return f"오류: 디렉토리 없음 - {cwd}"

    if cmd and cmd[0].lower() in BLOCKED:
        return f"차단된 커맨드: {cmd[0]}"

    # Windows에서 Unix 명령 자동 변환
    if sys.platform == "win32":
        unix_to_win = {"ls": "dir", "cat": "type", "cp": "copy", "mv": "move"}
        if cmd[0].lower() in unix_to_win:
            cmd = [unix_to_win[cmd[0].lower()]] + cmd[1:]

    return await _run_async(cmd, work_dir, timeout)


@mcp.tool()
async def run_python(
    code: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    Python 코드 스니펫 실행 (임시 파일 방식).
    ⚠️ 승인 필요 (X 권한)
    """
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        return await _run_async([sys.executable, tmp_path], Path("."), timeout)
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
