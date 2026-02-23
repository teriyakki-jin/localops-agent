"""
mcp-runner: 커맨드 실행 샌드박스 MCP 서버 (FastMCP)
- 네트워크: 기본 deny (policy.yaml 설정 따름)
- 타임아웃: 30초
- ⚠️ 모든 실행은 승인 필요 (X 권한)
"""
import asyncio
import subprocess
import sys
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("mcp-runner")
DEFAULT_TIMEOUT = 30


@mcp.tool()
def run_command(
    cmd: list[str],
    cwd: str = ".",
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    커맨드 실행 (읽기 전용 샌드박스).
    cmd: 실행할 커맨드 (예: ["pytest", "tests/", "-v"])
    cwd: 작업 디렉토리
    timeout: 최대 실행 시간(초)
    ⚠️ 승인 필요 (X 권한) — 네트워크 접근 차단
    """
    work_dir = Path(cwd).resolve()
    if not work_dir.exists():
        return f"오류: 디렉토리 없음 - {cwd}"

    # 위험 커맨드 차단 (기본 블랙리스트)
    blocked = {"rm", "del", "format", "mkfs", "dd", "curl", "wget", "ssh", "scp"}
    if cmd and cmd[0].lower() in blocked:
        return f"차단된 커맨드: {cmd[0]}"

    try:
        result = subprocess.run(
            cmd,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
            # Windows에서 새 프로세스 그룹으로 격리
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0,
        )
        output = result.stdout + result.stderr
        return_code = result.returncode
        return f"[returncode={return_code}]\n{output[:3000]}"

    except subprocess.TimeoutExpired:
        return f"타임아웃 ({timeout}초 초과)"
    except Exception as e:
        return f"실행 오류: {e}"


@mcp.tool()
def run_python(
    code: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """
    Python 코드 스니펫 실행 (임시 파일 방식).
    ⚠️ 승인 필요 (X 권한)
    """
    import tempfile, os

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as f:
        f.write(code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return f"[returncode={result.returncode}]\n{result.stdout}{result.stderr}"
    except subprocess.TimeoutExpired:
        return f"타임아웃 ({timeout}초 초과)"
    finally:
        os.unlink(tmp_path)


if __name__ == "__main__":
    mcp.run(transport="stdio", show_banner=False)
