from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    ok: bool
    message: str
    data: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False
    confirmation_token: str | None = None


@dataclass
class ToolContext:
    session_id: str
    memory: Any
    integrations: Any
    settings: Any
    permission_guard: Any = None
    confirmation_token: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolDefinition:
    name: str
    description: str
    schema_model: type[BaseModel]
    executor: Callable[[BaseModel, ToolContext], ToolResult]
    critical: bool = False
    permissions: set[str] = field(default_factory=set)

    def validate(self, payload: dict[str, Any]) -> BaseModel:
        return self.schema_model.model_validate(payload)

