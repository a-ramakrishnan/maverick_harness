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


class HarnessRunner:
    def __init__(self, agent: CodingAgent) -> None:
        self.agent = agent
        self._lock = asyncio.Lock()

    async def run_turn(self, user_prompt: str) -> AsyncIterator[HarnessEvent]:
    
        async with self._lock:
            limits = UsageLimits(request_limit=self.agent.max_steps)
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
                                        yield ToolCallStarted(
                                            tool_name=event.part.tool_name,
                                            args=str(event.part.args),
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
                    yield AssistantReply(text=str(run.result.output))

            except UsageLimitExceeded:
                yield RunError(
                    message=f"Reached max step limit ({self.agent.max_steps})."
                )
            except Exception as e:
                yield RunError(message=str(e))

    def reset(self) -> None:
        """Reset conversation history."""
        self.agent.reset()