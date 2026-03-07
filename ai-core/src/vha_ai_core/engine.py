from __future__ import annotations

from pydantic import BaseModel, Field

from vha_memory.models import ChatMessage
from vha_tools.base import ToolContext


class AssistantResponse(BaseModel):
    reply: str
    suggestions: list[dict] = Field(default_factory=list)
    tool_result: dict | None = None
    learned_items: list[dict] = Field(default_factory=list)
    requires_confirmation: bool = False
    confirmation_token: str | None = None
    reasoning: str = ""


class TukkieAssistantEngine:
    def __init__(self, *, settings, memory, vector_store, tool_registry, integrations, permission_guard, llm_client):
        from .knowledge import KnowledgeService
        from .learning import LearningEngine
        from .reasoning import DutchReasoningEngine

        self.settings = settings
        self.memory = memory
        self.vector_store = vector_store
        self.tool_registry = tool_registry
        self.integrations = integrations
        self.permission_guard = permission_guard
        self.llm_client = llm_client
        self.reasoning = DutchReasoningEngine()
        self.knowledge = KnowledgeService(memory, vector_store)
        self.learning = LearningEngine(memory, vector_store)

    async def handle_message(self, session_id: str, message: str, confirmation_token: str | None = None) -> AssistantResponse:
        self.memory.append_message(ChatMessage(session_id=session_id, role="user", content=message))
        learned_items = self.learning.learn_from_message(message)
        knowledge_bundle = self.knowledge.build_bundle(message)
        decision = self.reasoning.decide(message, knowledge_bundle)

        tool_result = None
        if decision.tool_name:
            tool_result = self.tool_registry.execute(
                decision.tool_name,
                decision.tool_args,
                ToolContext(
                    session_id=session_id,
                    memory=self.memory,
                    integrations=self.integrations,
                    settings=self.settings,
                    permission_guard=self.permission_guard,
                    confirmation_token=confirmation_token,
                    metadata={"reasoning": decision.explanation},
                ),
            )

        suggestions = self.learning.generate_suggestions()
        reply = await self._compose_reply(message, knowledge_bundle, tool_result, suggestions)

        response = AssistantResponse(
            reply=reply,
            suggestions=[suggestion.model_dump() for suggestion in suggestions[:4]],
            tool_result=tool_result.model_dump() if tool_result else None,
            learned_items=[item.model_dump() for item in learned_items],
            requires_confirmation=bool(tool_result and tool_result.requires_confirmation),
            confirmation_token=tool_result.confirmation_token if tool_result else None,
            reasoning=decision.explanation,
        )
        self.memory.append_message(
            ChatMessage(
                session_id=session_id,
                role="assistant",
                content=response.reply,
                metadata={"reasoning": decision.explanation, "tool": decision.tool_name},
            )
        )
        return response

    async def _compose_reply(self, message, knowledge_bundle, tool_result, suggestions) -> str:
        if tool_result is not None:
            if tool_result.requires_confirmation:
                return f"{tool_result.message} Gebruik de bevestigingstoken om deze kritieke actie expliciet te bevestigen."
            if tool_result.ok:
                suggestion_line = ""
                if suggestions:
                    suggestion_line = f" Ik zie daarnaast een patroon: {suggestions[0].description}"
                return f"{tool_result.message}{suggestion_line}"
            return tool_result.message

        context_prompt = self._build_context_prompt(knowledge_bundle, suggestions)
        llm_reply = await self.llm_client.generate(user_prompt=message, context_prompt=context_prompt)
        if llm_reply:
            return llm_reply

        profile_name = knowledge_bundle.profile.get("name", {}).get("value", self.settings.default_profile_name)
        suggestion_line = ""
        if suggestions:
            suggestion_line = f" Ik heb ook {len(suggestions)} routine-observatie(s) klaarstaan in je dashboard."
        return (
            f"{profile_name}, ik heb je vraag lokaal verwerkt. "
            f"Ik kan apparaten bedienen via veilige tools, routines analyseren en suggesties doen.{suggestion_line}"
        )

    @staticmethod
    def _build_context_prompt(knowledge_bundle, suggestions) -> str:
        room_names = ", ".join(room["name"] for room in knowledge_bundle.rooms)
        device_names = ", ".join(device["name"] for device in knowledge_bundle.devices[:8])
        automations = ", ".join(automation["name"] for automation in knowledge_bundle.automations[:6]) or "geen"
        suggestion_text = " | ".join(suggestion.description for suggestion in suggestions[:3]) or "geen suggesties"
        return (
            f"Ruimtes: {room_names}\n"
            f"Devices: {device_names}\n"
            f"Automatiseringen: {automations}\n"
            f"Recente suggesties: {suggestion_text}\n"
            f"Gerelateerde herinneringen: {knowledge_bundle.related_memories[:4]}"
        )
