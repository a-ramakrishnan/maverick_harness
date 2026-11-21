import asyncio
from collections.abc import AsyncIterator

from pydantic_ai import (
    Agent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    UsageLimitExceeded,
    UsageLimits,
)

from maverick_harness.agent.loop import CodingAgent
from maverick_harness.harness.events import (
    AssistantReply,
    HarnessEvent,
    RunError,
    ToolCallFinished,
    ToolCallStarted,
)

MAX_IDENTICAL_TOOL_CALLS = 3


class HarnessRunner:
    """Headless orchestrator that streams typed HarnessEvents for each turn."""

    def __init__(self, agent: CodingAgent) -> None:
        self.agent = agent
        self._lock = asyncio.Lock()

    async def run_turn(self, user_prompt: str) -> AsyncIterator[HarnessEvent]:
        """Run one user turn and yield live tool & reply events."""
        async with self._lock:
            limits = UsageLimits(request_limit=self.agent.max_steps)
            recent_calls: list[tuple[str, str]] = []

            try:
                async with self.agent._agent.iter(
                    user_prompt,
                    message_history=self.agent.message_history,
                    usage_limits=limits,
                ) as run:
                    async for node in run:
                        if Agent.is_call_tools_node(node):
                            async with node.stream(run.ctx) as stream:
                                async for event in stream:
                                    if isinstance(event, FunctionToolCallEvent):
                                        sig = (event.part.tool_name, str(event.part.args))
                                        recent_calls.append(sig)
                                        if (
                                            len(recent_calls) >= MAX_IDENTICAL_TOOL_CALLS
                                            and len(set(recent_calls[-MAX_IDENTICAL_TOOL_CALLS:])) == 1
                                        ):
                                            yield RunError(
                                                message=(
                                                    f"Doom-loop detected: '{sig[0]}' was called "
                                                    f"{MAX_IDENTICAL_TOOL_CALLS} times in a row with "
                                                    "identical arguments."
                                                )
                                            )
                                            return

                                        yield ToolCallStarted(
                                            tool_name=sig[0],
                                            args=sig[1],
                                        )
                                    elif isinstance(event, FunctionToolResultEvent):
                                        content = str(event.part.content)
                                        preview = (
                                            content[:200] + "..."
                                            if len(content) > 200
                                            else content
                                        )
                                        yield ToolCallFinished(
                                            tool_name=event.part.tool_name,
                                            output_preview=preview,
                                        )

                if run.result is not None:
                    self.agent.message_history = run.result.all_messages()
                    usage = run.result.usage
                    yield AssistantReply(
                        text=str(run.result.output),
                        input_tokens=getattr(usage, "input_tokens", 0) or 0,
                        output_tokens=getattr(usage, "output_tokens", 0) or 0,
                        requests=getattr(usage, "requests", 0) or 0,
                    )

            except UsageLimitExceeded:
                yield RunError(
                    message=f"Reached max step limit ({self.agent.max_steps})."
                )
            except Exception as e:  # noqa: BLE001
                yield RunError(message=str(e))

    def reset(self) -> None:
        """Reset conversation history."""
        self.agent.reset()