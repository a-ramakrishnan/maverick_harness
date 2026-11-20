from pathlib import Path

MAX_OUTPUT_CHARS = 15_000

def _resolve_path(path:str) -> Path:
    return (Path.cwd()/path).resolve()

def read_file(path: str, start_line: int = 1, end_line: int = 200) -> str:

    target = _resolve_path(path)
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
    numbered = [
        f"{i + 1:>4} | {lines[i]}" for i in range(start_idx, end_idx)
    ]
    header = f"[{path} — lines {start_idx + 1}..{end_idx} of {total}]\n"
    return (header + "\n".join(numbered))[:MAX_OUTPUT_CHARS]

def write_file(path: str, content: str) -> str:

    target = _resolve_path(path)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} chars to {path}"
    except Exception as e:
        return f"Error writing {path}: {e}"

def edit_file(path: str, old_text: str, new_text: str) -> str:

    target = _resolve_path(path)
    if not target.exists():
        return f"Error: file not found: {path}"
    content = target.read_text(encoding="utf-8")
    count = content.count(old_text)
    if count == 0:
        return f"Error: old_text not found in {path}. Read the file first to verify exact text."
    if count > 1:
        return f"Error: old_text matched {count} times in {path}. Provide more surrounding context."
    updated = content.replace(old_text, new_text, 1)
    target.write_text(updated, encoding="utf-8")
    return f"Successfully edited {path}"

def glob_files(pattern: str = "**/*") -> str:

    root = Path.cwd()
    ignored = {".git", ".venv", "__pycache__", "node_modules"}
    matches: list[str] = []
    for p in sorted(root.glob(pattern)):
        if any(part in ignored for part in p.parts):
            continue
        if p.is_file():
            matches.append(str(p.relative_to(root)))
    if not matches:
        return f"No files matched pattern: {pattern}"
    return "\n".join(matches[:200])
    
def grep_search(query: str, glob_pattern: str = "**/*") -> str:

    root = Path.cwd()
    ignored = {".git", ".venv", "__pycache__", "node_modules"}
    hits: list[str] = []
    for p in sorted(root.glob(glob_pattern)):
        if not p.is_file() or any(part in ignored for part in p.parts):
            continue
        try:
            for line_no, line in enumerate(
                p.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if query in line:
                    rel = p.relative_to(root)
                    hits.append(f"{rel}:{line_no}: {line.strip()}")
                    if len(hits) >= 100:
                        return "\n".join(hits) + "\n... (truncated at 100 matches)"
        except (UnicodeDecodeError, PermissionError):
            continue
    return "\n".join(hits) if hits else f"No matches found for '{query}'."