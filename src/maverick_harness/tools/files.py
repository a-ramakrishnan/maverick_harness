import re
from pathlib import Path

MAX_OUTPUT_CHARS = 12_000
IGNORED_DIRS = {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache"}
SECRET_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
SECRET_NAMES = {"id_rsa", "id_ed25519", "credentials.json"}


def _is_secret_path(path: Path) -> bool:
    """Return True if the file likely contains secrets (e.g. .env, private keys)."""
    name = path.name
    if name == ".env":
        return True
    if name.startswith(".env.") and name not in {".env.example", ".env.sample", ".env.template"}:
        return True
    if name in SECRET_NAMES or path.suffix.lower() in SECRET_SUFFIXES:
        return True
    return False


def _resolve_path(path: str) -> Path | str:
    """Resolve a path inside the workspace root and block secret files."""
    root = Path.cwd().resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        return f"Error: path '{path}' escapes workspace root."
    if _is_secret_path(target):
        return f"Error: access to sensitive file '{path}' is blocked."
    return target


def read_file(path: str, start_line: int = 1, end_line: int = 200) -> str:
    """Read a text file with line numbers.

    Args:
        path: Path to the file (relative to workspace root).
        start_line: 1-based starting line number (inclusive).
        end_line: 1-based ending line number (inclusive).
    """
    target = _resolve_path(path)
    if isinstance(target, str):
        return target
    if not target.exists():
        return f"Error: file not found: {path}"
    if target.is_dir():
        return f"Error: '{path}' is a directory. Use glob_files to list it."

    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except Exception as e:
        return f"Error reading {path}: {e}"

    total = len(lines)
    start_idx = max(0, start_line - 1)
    end_idx = min(total, end_line)
    numbered = [f"{i + 1:>4} | {lines[i]}" for i in range(start_idx, end_idx)]
    header = f"[{path} — lines {start_idx + 1}..{end_idx} of {total}]\n"
    return (header + "\n".join(numbered))[:MAX_OUTPUT_CHARS]


def write_file(path: str, content: str) -> str:
    """Create a new file or overwrite an existing file with full content.

    Args:
        path: Target file path (relative to workspace root).
        content: Complete text content to write.
    """
    target = _resolve_path(path)
    if isinstance(target, str):
        return target
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"Error writing {path}: {e}"


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace an exact snippet of text in an existing file.

    Args:
        path: Target file path (relative to workspace root).
        old_text: Exact existing text to find (must match once).
        new_text: Replacement text.
    """
    target = _resolve_path(path)
    if isinstance(target, str):
        return target
    if not target.exists():
        return f"Error: file not found: {path}"

    content = target.read_text(encoding="utf-8")
    count = content.count(old_text)
    if count == 0:
        # Give the LLM a concrete hint where the first non-empty line appears
        first_line = next((ln.strip() for ln in old_text.splitlines() if ln.strip()), "")
        hint = ""
        if first_line:
            near_lines = [
                str(i)
                for i, ln in enumerate(content.splitlines(), start=1)
                if first_line in ln
            ][:5]
            if near_lines:
                hint = f" Similar text found near line(s): {', '.join(near_lines)}."
        return (
            f"Error: old_text not found in {path}.{hint} "
            "Use read_file to inspect exact lines before retrying."
        )
    if count > 1:
        return (
            f"Error: old_text matched {count} times in {path}. "
            "Include more surrounding lines so the match is unique."
        )

    updated = content.replace(old_text, new_text, 1)
    target.write_text(updated, encoding="utf-8")
    return f"Successfully edited {path}"


def glob_files(pattern: str = "**/*") -> str:
    """Find files matching a glob pattern in the workspace.

    Args:
        pattern: Glob pattern (e.g. 'src/**/*.py', '*.toml').
    """
    root = Path.cwd().resolve()
    matches: list[str] = []

    for p in sorted(root.glob(pattern)):
        if any(part in IGNORED_DIRS for part in p.parts):
            continue
        if p.is_file() and not _is_secret_path(p):
            matches.append(str(p.relative_to(root)))

    if not matches:
        return f"No files matched pattern: {pattern}"
    return "\n".join(matches[:200])


def grep_search(pattern: str, glob_pattern: str = "**/*") -> str:
    """Search workspace files using a Python regular expression.

    Args:
        pattern: Regex pattern to search for (e.g. 'def create_model', 'class .*Event').
        glob_pattern: Limit search to files matching this glob (default: all files).
    """
    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"Error: invalid regex '{pattern}': {e}"

    root = Path.cwd().resolve()
    hits: list[str] = []

    for p in sorted(root.glob(glob_pattern)):
        if not p.is_file() or any(part in IGNORED_DIRS for part in p.parts) or _is_secret_path(p):
            continue
        try:
            for line_no, line in enumerate(
                p.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if regex.search(line):
                    rel = p.relative_to(root)
                    hits.append(f"{rel}:{line_no}: {line.strip()}")
                    if len(hits) >= 100:
                        return "\n".join(hits) + "\n... (truncated at 100 matches)"
        except (UnicodeDecodeError, PermissionError):
            continue

    return "\n".join(hits) if hits else f"No matches found for pattern '{pattern}'."