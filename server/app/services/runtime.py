from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from server.app.bootstrap import ROOT_DIR

from vha_ai_core import OllamaClient, TukkieAssistantEngine
from vha_config import AppSettings, build_cipher
from vha_integrations import IntegrationManager
from vha_memory import MemoryStore, VectorMemoryStore
from vha_memory.models import NetworkSnapshot
from vha_tools import ToolRegistry, build_default_tools

from ..core.security import ActionConfirmationManager, ToolPermissionGuard
from .config_sync import sync_runtime_configuration
from .voice import VoiceService


@dataclass
class RuntimeContainer:
    settings: AppSettings
    memory: MemoryStore
    vector_store: VectorMemoryStore
    integrations: IntegrationManager
    tool_registry: ToolRegistry
    permission_guard: ToolPermissionGuard
    assistant: TukkieAssistantEngine
    config_summary: dict
    voice: VoiceService
    last_device_refresh: datetime | None = None
    last_ollama_check: datetime | None = None
    cached_ollama_available: bool = False

    def refresh_network_snapshot(self) -> dict:
        snapshot_data = self.integrations.network.snapshot()
        snapshot = self.memory.save_network_snapshot(
            NetworkSnapshot(
                devices=snapshot_data["devices"],
                traffic=snapshot_data["traffic"],
                anomaly_score=snapshot_data["anomaly_score"],
                summary=snapshot_data["summary"],
            )
        )
        return snapshot.model_dump()

    def refresh_device_states(self, force: bool = False) -> list[dict]:
        now = datetime.now(timezone.utc)
        if (
            not force
            and self.last_device_refresh is not None
            and now - self.last_device_refresh < timedelta(seconds=self.settings.device_refresh_interval_seconds)
        ):
            return [device.model_dump() for device in self.memory.list_devices()]

        refreshed_devices = []
        for device in self.memory.list_devices():
            status_payload = self.integrations.get_device_status(device.model_dump())
            state_patch = status_payload.get("state", {}) or {}
            updated = self.memory.update_device_state(
                device.id,
                state_patch,
                status=status_payload.get("status", device.status),
            )
            refreshed_devices.append((updated or device).model_dump())

        self.last_device_refresh = now
        return refreshed_devices

    def setup_status(self) -> dict:
        now = datetime.now(timezone.utc)
        if (
            self.last_ollama_check is None
            or now - self.last_ollama_check >= timedelta(seconds=30)
        ):
            self.cached_ollama_available = self.assistant.llm_client.available()
            self.last_ollama_check = now

        config_paths = {
            "assistant": self.settings.assistant_config_path,
            "profile": self.settings.profile_config_path,
            "rooms": self.settings.rooms_config_path,
            "devices": self.settings.devices_config_path,
            "scenes": self.settings.scenes_config_path,
            "automations": self.settings.automations_config_path,
        }
        return {
            "config": {
                "summary": self.config_summary,
                "files": [
                    {"name": name, "path": str(path), "exists": path.exists()}
                    for name, path in config_paths.items()
                ],
            },
            "ollama": {
                "available": self.cached_ollama_available,
                "host": self.settings.ollama_host,
                "model": self.settings.ollama_model,
            },
            "voice": self.voice.status(),
            "integrations": self.integrations.health(),
        }

    def dashboard_overview(self) -> dict:
        self.refresh_device_states()
        overview = self.memory.get_overview()
        network = overview["network"] or self.refresh_network_snapshot()
        devices = overview["devices"]
        rooms = overview["rooms"]
        profile = overview["profile"]
        assistant_name = profile.get("assistant_name", {}).get("value", self.settings.app_name)
        assistant_language = profile.get("assistant_language", {}).get("value", self.settings.default_language)
        assistant_wake_word = profile.get("assistant_wake_word", {}).get("value", self.settings.default_wake_word)
        cameras = [device for device in devices if device["type"] == "camera"]
        lights_on = sum(1 for device in devices if device["type"] == "light" and device["state"].get("power") == "on")
        devices_online = sum(1 for device in devices if device["status"] == "online")
        active_cameras = sum(1 for device in cameras if device["state"].get("recording"))
        estimated_watts = max(len(devices), 1) * 52 + (lights_on + active_cameras) * 37
        integrations_health = self.integrations.health()
        setup = self.setup_status()

        return {
            "assistant": {
                "name": assistant_name,
                "language": assistant_language,
                "model": self.settings.ollama_model,
                "wake_word": assistant_wake_word,
                "local_only": True,
                "voice_ready": self.settings.enable_voice_blueprint,
                "ollama_available": setup["ollama"]["available"],
            },
            "home_status": {
                "rooms_online": len(rooms),
                "devices_online": devices_online,
                "lights_on": lights_on,
                "automation_count": len(overview["automations"]),
                "integrations_connected": sum(1 for item in integrations_health if item.get("connected")),
            },
            "rooms": rooms,
            "devices": devices,
            "scenes": overview["scenes"],
            "automations": overview["automations"],
            "suggestions": overview["suggestions"],
            "activity": self.memory.get_recent_activity(limit=12),
            "cameras": cameras,
            "energy": {
                "estimated_watts": estimated_watts,
                "active_devices": lights_on + active_cameras,
                "window": "24h",
            },
            "network": network,
            "integrations": integrations_health,
            "profile": profile,
            "voice": self.voice.status(),
            "setup": setup,
            "project_root": str(ROOT_DIR),
        }


def build_runtime() -> RuntimeContainer:
    settings = AppSettings()
    settings.ensure_directories()

    cipher = build_cipher(settings.memory_encryption_key)
    memory = MemoryStore(settings.db_path, cipher=cipher)
    memory.initialize()

    vector_store = VectorMemoryStore(settings.chroma_path)
    integrations = IntegrationManager(allow_fallback=settings.allow_fallback_integrations)
    config_summary = sync_runtime_configuration(memory, settings)

    tool_registry = ToolRegistry()
    tool_registry.register_many(build_default_tools())

    confirmation_manager = ActionConfirmationManager(settings.critical_confirmation_window_seconds)
    permission_guard = ToolPermissionGuard(confirmation_manager)
    llm_client = OllamaClient(settings.ollama_host, settings.ollama_model, settings.prompt_path)
    voice = VoiceService(settings)

    assistant = TukkieAssistantEngine(
        settings=settings,
        memory=memory,
        vector_store=vector_store,
        tool_registry=tool_registry,
        integrations=integrations,
        permission_guard=permission_guard,
        llm_client=llm_client,
    )

    return RuntimeContainer(
        settings=settings,
        memory=memory,
        vector_store=vector_store,
        integrations=integrations,
        tool_registry=tool_registry,
        permission_guard=permission_guard,
        assistant=assistant,
        config_summary=config_summary,
        voice=voice,
    )
