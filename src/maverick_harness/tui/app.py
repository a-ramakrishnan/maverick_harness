from pathlib import Path

from prompt_toolkit import PromptSession
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from maverick_harness.harness.events import (
    AssistantReply,
    RunError,
    ToolCallFinished,
    ToolCallStarted,
)
from maverick_harness.harness.runner import HarnessRunner


async def run_tui(runner: HarnessRunner, *, read_only: bool = False) -> None:
    """Interactive terminal REPL connected to the headless HarnessRunner."""
    console = Console()
    session: PromptSession[str] = PromptSession()

    mode_label = "read-only" if read_only else "full (read/write/bash)"
    console.print(
        Panel.fit(
            f"[bold cyan]Maverick Harness[/bold cyan]\n"
            f"[dim]Model:[/dim] {runner.agent.model_spec}   "
            f"[dim]Mode:[/dim] {mode_label}\n"
            f"[dim]Workspace:[/dim] {Path.cwd()}\n"
            f"[dim]Commands:[/dim] /clear to reset history, /exit to quit",
            border_style="cyan",
        )
    )

    while True:
        try:
            user_input = (await session.prompt_async("\nyou > ")).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not user_input:
            continue
        if user_input in {"/exit", "/quit"}:
            console.print("[dim]Goodbye![/dim]")
            break
        if user_input == "/clear":
            runner.reset()
            console.print("[yellow]Conversation history cleared.[/yellow]")
            continue

        console.print()
        async for event in runner.run_turn(user_input):
            if isinstance(event, ToolCallStarted):
                console.print(
                    f"  [bold yellow]⚡ {event.tool_name}[/bold yellow] "
                    f"[dim]{event.args}[/dim]"
                )
            elif isinstance(event, ToolCallFinished):
                first_line = event.output_preview.splitlines()[0] if event.output_preview else ""
                console.print(f"  [green]✓ {event.tool_name}[/green] [dim]{first_line[:100]}[/dim]")
            elif isinstance(event, AssistantReply):
                console.print(
                    Panel(
                        Markdown(event.text),
                        title="[bold cyan]maverick[/bold cyan]",
                        border_style="blue",
                    )
                )
            elif isinstance(event, RunError):
                console.print(f"[bold red]Error:[/bold red] {event.message}")