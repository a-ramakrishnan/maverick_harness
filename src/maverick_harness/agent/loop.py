from pydantic_ai import Agent, UsageLimitExceeded, UsageLimits
from pydantic_ai.messages import ModelMessage

from maverick_harness.agent.factory import DEFAULT_MODEL, create_model
from maverick_harness.agent.prompts import build_system_prompt
from maverick_harness.tools.registry import get_tools


class CodingAgent:
    """Core ReAct loop wrapping a Pydantic AI Agent with coding tools & history."""

    def __init__(
        self,
        model_spec: str = DEFAULT_MODEL,
        *,
        read_only: bool = False,
        max_steps: int = 25,
    ) -> None:
        self.model_spec = model_spec
        self.max_steps = max_steps
        self.message_history: list[ModelMessage] = []

        self._agent = Agent(
            model=create_model(model_spec),
            instructions=build_system_prompt(read_only=read_only),
        )
        for tool_fn in get_tools(read_only=read_only):
            self._agent.tool_plain(tool_fn)

    def run_turn(self, user_prompt: str) -> str:
        """Run one user turn (may execute multiple LLM <-> tool steps internally)."""
        limits = UsageLimits(request_limit=self.max_steps)
        try:
            result = self._agent.run_sync(
                user_prompt,
                message_history=self.message_history,
                usage_limits=limits,
            )
        except UsageLimitExceeded:
            return f"[Stopped: reached max step limit ({self.max_steps})]"

        self.message_history = result.all_messages()
        return result.output

    def reset(self) -> None:
        """Clear conversation history to start a fresh session."""
        self.message_history = []