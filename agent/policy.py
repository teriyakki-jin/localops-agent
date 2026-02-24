"""
승인/권한 모델
- 권한 티어: R(읽기), W(쓰기), X(실행), N(네트워크), S(민감)
- W/X/N 는 기본 승인 필수
"""
from enum import Enum
from typing import Any
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


class Permission(str, Enum):
    R = "R"  # Read
    W = "W"  # Write
    X = "X"  # Execute
    N = "N"  # Network
    S = "S"  # Sensitive


# 툴 이름 → 필요 권한 매핑
TOOL_PERMISSIONS: dict[str, list[Permission]] = {
    # fs
    "read_file": [Permission.R],
    "list_dir": [Permission.R],
    "write_file": [Permission.W],
    "apply_patch": [Permission.W],
    "move_file": [Permission.W],
    # git
    "git_log": [Permission.R],
    "git_diff": [Permission.R],
    "git_status": [Permission.R],
    "create_branch": [Permission.W],
    "git_commit": [Permission.W],
    "open_pr": [Permission.W, Permission.N],
    # notes
    "read_note": [Permission.R],
    "search_notes": [Permission.R],
    "create_note": [Permission.W],
    "append_note": [Permission.W],
    # runner
    "run_command": [Permission.X],
}

# 이번 세션에서 사전 승인된 (tool, 인자 패턴) 목록
_session_approvals: set[str] = set()


def _approval_key(tool_name: str, context_hint: str = "") -> str:
    return f"{tool_name}::{context_hint}"


def requires_approval(tool_name: str) -> bool:
    perms = TOOL_PERMISSIONS.get(tool_name, [])
    return any(p in (Permission.W, Permission.X, Permission.N) for p in perms)


def is_session_approved(tool_name: str, context_hint: str = "") -> bool:
    return _approval_key(tool_name, context_hint) in _session_approvals


def request_approval(
    tool_name: str,
    arguments: dict[str, Any],
    reason: str = "",
    preview: str = "",
    context_hint: str = "",
) -> bool:
    """
    터미널에서 사용자에게 승인 요청.
    Returns True if approved.
    """
    if is_session_approved(tool_name, context_hint):
        return True

    console.print()
    console.print(Panel(
        f"[bold yellow]툴 호출 승인 요청[/bold yellow]\n\n"
        f"[bold]툴:[/bold] {tool_name}\n"
        f"[bold]이유:[/bold] {reason or '(없음)'}\n"
        f"[bold]인자:[/bold] {arguments}",
        title="[red]승인 필요[/red]",
        border_style="yellow",
    ))

    if preview:
        console.print(Panel(
            Syntax(preview, "diff", theme="monokai"),
            title="미리보기",
            border_style="blue",
        ))

    console.print("[1] 이번 한 번만 허용")
    console.print("[2] 이 툴은 세션 동안 허용")
    console.print("[3] 거부")
    try:
        choice = console.input("\n선택 (1/2/3): ").strip()
    except EOFError:
        console.print("[red]stdin 없음 - 자동 거부됨.[/red]")
        return False

    if choice == "1":
        return True
    elif choice == "2":
        _session_approvals.add(_approval_key(tool_name, context_hint))
        return True
    else:
        console.print("[red]거부됨.[/red]")
        return False
