import platform
import shutil
import sys
from pathlib import Path

IGNORED_TOP_LEVEL = {".git", ".venv", "__pycache__", "node_modules", ".env"}
PROBED_BINARIES = ("git", "python3", "uv", "pytest", "ruff", "gcc", "rg", "docker")


def _build_env_snapshot(cwd: Path) -> str:
    """Gather a tiny, deterministic snapshot of the workspace & runtime."""
    available = [b for b in PROBED_BINARIES if shutil.which(b)]
    entries: list[str] = []
    for p in sorted(cwd.iterdir()):
        if p.name in IGNORED_TOP_LEVEL or (p.name.startswith(".env.") and p.name != ".env.example"):
            continue
        entries.append(f"{p.name}/" if p.is_dir() else p.name)

    return "\n".join(
        [
            f"- OS: {platform.system()} ({platform.machine()})",
            f"- Python: {sys.version.split()[0]}",
            f"- Available CLIs: {', '.join(available) or 'none'}",
            f"- Top-level entries: {', '.join(entries[:30]) or '(empty)'}",
        ]
    )


def build_system_prompt(
    workspace: Path | None = None,
    *,
    read_only: bool = False,
) -> str:
    """Build the core system instructions for the coding agent."""
    cwd = (workspace or Path.cwd()).resolve()
    env_snapshot = _build_env_snapshot(cwd)

    if read_only:
        workflow = """\
Mode: READ-ONLY (file writes and shell commands are disabled).

Core workflow:
1. Inspect thoroughly: use `glob_files`, `grep_search`, and `read_file` to understand the codebase before answering or proposing changes.
2. Don't repeat failing calls: if a tool call fails or returns unexpected output, change your approach instead of retrying identical arguments.
3. Be concise and factual: cite exact file paths and line numbers. Never claim to have edited files or run commands."""
    else:
        workflow = """\
Core workflow:
1. Inspect before acting: use `glob_files`, `grep_search`, and `read_file` to understand the codebase before proposing or making changes.
2. Make surgical edits: prefer `edit_file` over rewriting whole files with `write_file`.
3. Verify your work: after editing code, run relevant checks (tests, linter, or a quick command via `run_bash`) before claiming success.
4. Don't repeat failing calls: if a tool call fails or returns unexpected output, change your approach instead of retrying identical arguments.
5. Be concise and factual: cite exact file paths and report real command outputs. Never invent files or test results."""

    return f"""\
You are Maverick, a disciplined terminal coding agent operating in: {cwd}

Environment snapshot:
{env_snapshot}

{workflow}
"""