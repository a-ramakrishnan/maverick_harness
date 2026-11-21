from pydantic import BaseModel


class ToolCallStarted(BaseModel):
    tool_name: str
    args: str


class ToolCallFinished(BaseModel):
    tool_name: str
    output_preview: str


class AssistantReply(BaseModel):
    """Emitted with the agent's final response and usage metrics for the turn."""

    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    requests: int = 0


class RunError(BaseModel):
    message: str


HarnessEvent = ToolCallStarted | ToolCallFinished | AssistantReply | RunError