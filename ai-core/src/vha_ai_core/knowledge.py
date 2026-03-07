from __future__ import annotations

from pydantic import BaseModel, Field


class KnowledgeBundle(BaseModel):
    profile: dict = Field(default_factory=dict)
    rooms: list[dict] = Field(default_factory=list)
    devices: list[dict] = Field(default_factory=list)
    scenes: list[dict] = Field(default_factory=list)
    automations: list[dict] = Field(default_factory=list)
    related_memories: list[dict] = Field(default_factory=list)


class KnowledgeService:
    def __init__(self, memory, vector_store):
        self.memory = memory
        self.vector_store = vector_store

    def build_bundle(self, message: str) -> KnowledgeBundle:
        related_memories = [
            memory.model_dump() for memory in self.memory.search_long_term_memory(message, limit=4)
        ]
        related_memories.extend(self.vector_store.query(message, limit=4))
        return KnowledgeBundle(
            profile=self.memory.get_user_profile(),
            rooms=[room.model_dump() for room in self.memory.list_rooms()],
            devices=[device.model_dump() for device in self.memory.list_devices()],
            scenes=[scene.model_dump() for scene in self.memory.list_scenes()],
            automations=[automation.model_dump() for automation in self.memory.list_automations()],
            related_memories=related_memories,
        )

