from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatMessage(BaseModel):
    id: int | None = None
    session_id: str = "default"
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)


class LongTermMemory(BaseModel):
    id: int | None = None
    category: str
    title: str
    content: str
    importance: float = 0.5
    tags: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)


class RoomState(BaseModel):
    id: str
    name: str
    purpose: str = ""
    status: str = "online"
    metrics: dict[str, Any] = Field(default_factory=dict)


class DeviceState(BaseModel):
    id: str
    name: str
    room: str
    type: str
    vendor: str = "generic"
    integration: str = "generic"
    status: str = "unknown"
    state: dict[str, Any] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SceneState(BaseModel):
    id: str
    name: str
    room: str
    state: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AutomationRule(BaseModel):
    id: str
    name: str
    description: str
    trigger: dict[str, Any]
    action: dict[str, Any]
    enabled: bool = True
    confidence: float = 0.5
    metadata: dict[str, Any] = Field(default_factory=dict)


class InteractionEvent(BaseModel):
    id: int | None = None
    event_type: str
    timestamp: str = Field(default_factory=utc_now)
    room: str | None = None
    device_id: str | None = None
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)


class AutomationSuggestion(BaseModel):
    id: int | None = None
    title: str
    description: str
    confidence: float = 0.5
    status: Literal["open", "accepted", "dismissed"] = "open"
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)


class NetworkSnapshot(BaseModel):
    id: int | None = None
    created_at: str = Field(default_factory=utc_now)
    devices: list[dict[str, Any]] = Field(default_factory=list)
    traffic: dict[str, Any] = Field(default_factory=dict)
    anomaly_score: float = 0.0
    summary: str = ""

