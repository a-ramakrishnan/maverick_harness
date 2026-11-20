import subprocess

MAX_OUTPUT_CHARS = 15_000

def run_bash(command:str, timeout:int = 30) -> str:

    try:
        result = subprocess.run(command, shell = True, capture_output=True, text=True, timeout=timeout)

    except subprocess.TimeoutExpired:
        return f"Error: command timed out after {timeout}s: {command}"

    except Exception as e:
        return f"Error: executing command: {e}"
    
    parts = [f"exit_code: {result.returncode}"]

    if result.stdout:
        parts.append(f"--- stdout ---\n{result.stdout.strip()}")
    if result.stderr:
        parts.append(f"--- stderr ---\n{result.stderr.strip()}")
    output = "\n".join(parts)
    if len(output) > MAX_OUTPUT_CHARS:
        return output[:MAX_OUTPUT_CHARS] + "\n... (output truncated)"
    return output

