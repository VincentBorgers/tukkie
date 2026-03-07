from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str
    confirmation_token: str | None = None


class ToolExecutionRequest(BaseModel):
    payload: dict = Field(default_factory=dict)
    confirmation_token: str | None = None


class ChatResponse(BaseModel):
    reply: str
    suggestions: list[dict] = Field(default_factory=list)
    tool_result: dict | None = None
    learned_items: list[dict] = Field(default_factory=list)
    requires_confirmation: bool = False
    confirmation_token: str | None = None
    reasoning: str = ""


class SpeakRequest(BaseModel):
    text: str


class VoiceTranscriptionResponse(BaseModel):
    transcript: str
    sample_rate: int
    channels: int
    seconds: float
    words: list[dict] = Field(default_factory=list)
