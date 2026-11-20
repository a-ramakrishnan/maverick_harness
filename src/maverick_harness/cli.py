import asyncio
import os
import click
from maverick_harness.agent.factory import DEFAULT_MODEL
from maverick_harness.agent.loop import CodingAgent
from maverick_harness.harness.runner import HarnessRunner
from maverick_harness.tui.app import run_tui

@click.command()
@click.option(
    "--model",
    default="openai:gpt-5-mini",
    show_default=True,
    help="LLm model to use in the coding agent",
)

@click.option(
    "--read-only",
    is_flag=True,
    default=False,
    help="Restrict the agent to read-only tools (no file writes or bash).",
)
def main(model: str, read_only: bool) -> None:
    """Maverick Harness — a coding agent built from scratch."""
    os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
    agent = CodingAgent(model_spec=model, read_only=read_only)
    runner = HarnessRunner(agent)
    asyncio.run(run_tui(runner, read_only=read_only))

if __name__ == "__main__":
    main()