import asyncio
import os
import sys
from pathlib import Path

import click

from maverick_harness.agent.factory import DEFAULT_MODEL
from maverick_harness.agent.loop import CodingAgent
from maverick_harness.harness.events import (
    AssistantReply,
    RunError,
    ToolCallStarted,
)
from maverick_harness.harness.runner import HarnessRunner
from maverick_harness.harness.trace import TraceLogger
from maverick_harness.tui.app import run_tui


async def _run_headless(
    runner: HarnessRunner,
    prompt: str,
    trace_path: Path | None = None,
) -> int:
    """Execute one non-interactive turn (ideal for benchmarks & CI). Returns exit code."""
    tracer = TraceLogger(trace_path) if trace_path else None
    exit_code = 0

    async for event in runner.run_turn(prompt):
        if tracer:
            tracer.log_event(event)

        if isinstance(event, ToolCallStarted):
            click.echo(f"[tool] {event.tool_name} {event.args}", err=True)
        elif isinstance(event, AssistantReply):
            click.echo(event.text)
            click.echo(
                f"[usage] steps={event.requests} "
                f"in={event.input_tokens} out={event.output_tokens}",
                err=True,
            )
        elif isinstance(event, RunError):
            click.echo(f"[error] {event.message}", err=True)
            exit_code = 1

    return exit_code


@click.command()
@click.option(
    "--model",
    default=DEFAULT_MODEL,
    show_default=True,
    help="Model spec in 'provider:model' format.",
)
@click.option(
    "--read-only",
    is_flag=True,
    default=False,
    help="Restrict the agent to read-only tools (no file writes or bash).",
)
@click.option(
    "--max-steps",
    default=25,
    show_default=True,
    type=int,
    help="Maximum LLM/tool request steps per turn.",
)
@click.option(
    "--prompt",
    default=None,
    help="Run one non-interactive headless turn and exit (for benchmarks/CI).",
)
@click.option(
    "--trace",
    type=click.Path(path_type=Path),
    default=None,
    help="Write a JSONL trajectory log of all HarnessEvents to this path.",
)
def main(
    model: str,
    read_only: bool,
    max_steps: int,
    prompt: str | None,
    trace: Path | None,
) -> None:
    """Maverick Harness — a coding agent built from scratch."""
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

    agent = CodingAgent(model_spec=model, read_only=read_only, max_steps=max_steps)
    runner = HarnessRunner(agent)

    if prompt is not None:
        code = asyncio.run(_run_headless(runner, prompt, trace_path=trace))
        sys.exit(code)

    asyncio.run(run_tui(runner, read_only=read_only))


if __name__ == "__main__":
    main()