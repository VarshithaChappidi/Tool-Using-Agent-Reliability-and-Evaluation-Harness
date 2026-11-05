from typing import Literal
from pydantic import BaseModel, Field

class AgentRequest(BaseModel):
    ticket_id: str = Field(min_length=1)
    user_message: str = Field(min_length=3)
    scenario: Literal["normal", "timeout_once", "timeout_always", "malformed", "ambiguous", "prompt_injection"] = "normal"

class ToolResult(BaseModel):
    ok: bool
    ticket_id: str
    status: str | None = None
    error: str | None = None
    retryable: bool = False

class AgentOutcome(BaseModel):
    status: Literal["completed", "needs_clarification", "blocked", "tool_failed"]
    summary: str
    proposed_action: str | None = None
    approval_required: bool = True
    attempts: int = 0
    errors: list[str] = []
