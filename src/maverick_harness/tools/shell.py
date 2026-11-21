import subprocess
from pathlib import Path

HEAD_CHARS = 4_000
TAIL_CHARS = 11_000
MAX_OUTPUT_CHARS = HEAD_CHARS + TAIL_CHARS
MIN_TIMEOUT_SECONDS = 1
MAX_TIMEOUT_SECONDS = 120

def _truncate_head_tail(text: str) -> str:
    
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    omitted = len(text) - MAX_OUTPUT_CHARS
    return (
        text[:HEAD_CHARS]
        + f"\n\n... [{omitted:,} chars omitted from middle] ...\n\n"
        + text[-TAIL_CHARS:]
    )

def _resolve_workdir(workdir: str) -> Path | str:
    
    root = Path.cwd().resolve()
    target = (root / workdir).resolve()
    if not target.is_relative_to(root):
        return f"Error: workdir '{workdir}' escapes workspace root."
    if not target.exists() or not target.is_dir():
        return f"Error: workdir does not exist or is not a directory: '{workdir}'."
    return target


def run_bash(command:str, workdir: str = ".",timeout_seconds:int = 30) -> str:

    cwd = _resolve_workdir(workdir)
    if isinstance(cwd, str):
        return cwd
    
    clamped_timeout = max(MIN_TIMEOUT_SECONDS, min(timeout_seconds, MAX_TIMEOUT_SECONDS))

    try:
        result = subprocess.run(command, shell = True, cwd = cwd, capture_output=True, text=True, timeout=clamped_timeout)

    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {clamped_timeout}s: {command}"

    except Exception as e:
        return f"Error: executing command: {e}"
    
    parts = [f"exit_code: {result.returncode}"]

    if result.stdout:
        parts.append(f"--- stdout ---\n{result.stdout.strip()}")
    if result.stderr:
        parts.append(f"--- stderr ---\n{result.stderr.strip()}")
    #output = "\n".join(parts)
    #if len(output) > MAX_OUTPUT_CHARS:
    #    return output[:MAX_OUTPUT_CHARS] + "\n... (output truncated)"

    #return output
    return _truncate_head_tail("\n".join(parts))

