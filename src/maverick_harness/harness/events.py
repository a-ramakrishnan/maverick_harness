from pydantic import BaseModel

class ToolCallStarted(BaseModel):
    tool_name: str
    args: str

class ToolCallFinished(BaseModel):
    tool_name: str
    output_preview: str

class AssistantReply(BaseModel):
    text: str

class RunError(BaseModel):
    message: str

HarnessEvent = ToolCallStarted | ToolCallFinished | AssistantReply | RunError

