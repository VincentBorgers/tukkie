from __future__ import annotations

from typing import Any

from .base import ToolContext, ToolDefinition, ToolResult


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        self._tools[definition.name] = definition

    def register_many(self, definitions: list[ToolDefinition]) -> None:
        for definition in definitions:
            self.register(definition)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": definition.name,
                "description": definition.description,
                "critical": definition.critical,
                "schema": definition.schema_model.model_json_schema(),
            }
            for definition in sorted(self._tools.values(), key=lambda item: item.name)
        ]

    def execute(self, tool_name: str, payload: dict[str, Any], context: ToolContext) -> ToolResult:
        definition = self._tools.get(tool_name)
        if definition is None:
            return ToolResult(ok=False, message=f"Onbekende tool: {tool_name}")

        validated_payload = definition.validate(payload)
        if context.permission_guard is not None:
            decision = context.permission_guard.authorize(
                tool_name=definition.name,
                critical=definition.critical,
                payload=validated_payload.model_dump(),
                confirmation_token=context.confirmation_token,
            )
            if not decision["allowed"]:
                return ToolResult(
                    ok=False,
                    message=decision["message"],
                    requires_confirmation=decision.get("requires_confirmation", False),
                    confirmation_token=decision.get("confirmation_token"),
                )

        return definition.executor(validated_payload, context)
