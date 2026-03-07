from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from vha_memory.models import AutomationSuggestion, LongTermMemory


class LearningEngine:
    def __init__(self, memory, vector_store):
        self.memory = memory
        self.vector_store = vector_store

    def learn_from_message(self, message: str) -> list[LongTermMemory]:
        lowered = message.lower()
        learned: list[LongTermMemory] = []

        if "nederlands" in lowered:
            record = LongTermMemory(
                category="preference",
                title="Gebruiker wil Nederlands",
                content="De gebruiker wil dat Tukkie Nederlands spreekt.",
                importance=0.92,
                tags=["language", "preference"],
            )
            self.memory.save_long_term_memory(record)
            self.vector_store.upsert(f"memory-{record.id}", record.content, {"category": record.category})
            learned.append(record)

        if "film" in lowered or "movie mode" in lowered:
            record = LongTermMemory(
                category="habit",
                title="Filmroutine genoemd",
                content="De gebruiker heeft een voorkeur of interesse in een filmroutine of movie mode.",
                importance=0.7,
                tags=["habit", "movie-mode"],
            )
            self.memory.save_long_term_memory(record)
            self.vector_store.upsert(f"memory-{record.id}", record.content, {"category": record.category})
            learned.append(record)

        return learned

    def generate_suggestions(self) -> list[AutomationSuggestion]:
        interactions = self.memory.get_recent_interactions(limit=120)
        buckets: dict[tuple[str | None, str | None, str, int], int] = defaultdict(int)

        for event in interactions:
            try:
                hour = datetime.fromisoformat(event.timestamp).hour
            except ValueError:
                hour = 0
            buckets[(event.room, event.device_id, event.action, hour)] += 1

        suggestions: list[AutomationSuggestion] = []
        for (room, device_id, action, hour), count in buckets.items():
            if count < 3:
                continue

            device_name = None
            if device_id:
                device = self.memory.get_device(device_id)
                device_name = device.name if device else device_id

            if action.startswith("scene:"):
                description = f"Ik zie dat je vaak een scene in {room or 'huis'} activeert rond {hour:02d}:00. Zal ik daar een automatisering van maken?"
            elif action.startswith("lights:"):
                description = f"Ik merk dat {device_name or 'de verlichting'} vaak rond {hour:02d}:00 wordt aangepast. Wil je dat ik dit automatiseer?"
            else:
                description = f"Ik zie een terugkerende actie '{action}' rond {hour:02d}:00. Wil je hiervoor een automatisering?"

            suggestions.append(
                AutomationSuggestion(
                    title=f"Routine ontdekt rond {hour:02d}:00",
                    description=description,
                    confidence=min(0.95, 0.55 + count * 0.08),
                    metadata={"room": room, "device_id": device_id, "action": action, "hour": hour},
                )
            )

        for suggestion in suggestions:
            self.memory.upsert_suggestion(suggestion)

        return suggestions
