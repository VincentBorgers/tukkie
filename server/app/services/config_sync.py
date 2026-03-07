from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from vha_memory.models import AutomationRule, DeviceState, RoomState, SceneState


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {}
    return data


def _room_from_entry(entry: dict[str, Any]) -> RoomState:
    return RoomState(
        id=entry["id"],
        name=entry["name"],
        purpose=entry.get("purpose", ""),
        status=entry.get("status", "configured"),
        metrics=entry.get("metrics", {}),
    )


def _device_from_entry(entry: dict[str, Any]) -> DeviceState:
    return DeviceState(
        id=entry["id"],
        name=entry["name"],
        room=entry["room"],
        type=entry["type"],
        vendor=entry.get("vendor", "generic"),
        integration=entry.get("integration", "generic"),
        status=entry.get("status", "configured"),
        state=entry.get("state", {}),
        capabilities=entry.get("capabilities", []),
        metadata=entry.get("metadata", {}),
    )


def _scene_from_entry(entry: dict[str, Any]) -> SceneState:
    return SceneState(
        id=entry["id"],
        name=entry["name"],
        room=entry["room"],
        state=entry.get("state", {}),
        metadata=entry.get("metadata", {}),
    )


def _automation_from_entry(entry: dict[str, Any]) -> AutomationRule:
    return AutomationRule(
        id=entry["id"],
        name=entry["name"],
        description=entry.get("description", ""),
        trigger=entry.get("trigger", {}),
        action=entry.get("action", {}),
        enabled=entry.get("enabled", True),
        confidence=entry.get("confidence", 0.5),
        metadata=entry.get("metadata", {}),
    )


def sync_runtime_configuration(memory, settings) -> dict[str, Any]:
    assistant_file = _load_yaml(settings.assistant_config_path)
    assistant_doc = assistant_file.get("assistant", {})
    voice_doc = assistant_file.get("voice", {}) if isinstance(assistant_file.get("voice", {}), dict) else {}
    if isinstance(assistant_doc.get("voice", {}), dict):
        voice_doc = {**voice_doc, **assistant_doc.get("voice", {})}
    storage_doc = assistant_file.get("storage", {})
    profile_doc = _load_yaml(settings.profile_config_path).get("profile", {})
    rooms_doc = _load_yaml(settings.rooms_config_path).get("rooms", [])
    devices_doc = _load_yaml(settings.devices_config_path).get("devices", [])
    scenes_doc = _load_yaml(settings.scenes_config_path).get("scenes", [])
    automations_doc = _load_yaml(settings.automations_config_path).get("automations", [])

    rooms = [_room_from_entry(entry) for entry in rooms_doc if entry.get("id") and entry.get("name")]
    devices = [
        _device_from_entry(entry)
        for entry in devices_doc
        if entry.get("id") and entry.get("name") and entry.get("room") and entry.get("type")
    ]
    scenes = [_scene_from_entry(entry) for entry in scenes_doc if entry.get("id") and entry.get("name") and entry.get("room")]
    automations = [
        _automation_from_entry(entry)
        for entry in automations_doc
        if entry.get("id") and entry.get("name")
    ]

    if settings.rooms_config_path.exists():
        memory.replace_rooms(rooms)
    if settings.devices_config_path.exists():
        memory.sync_devices_from_config(devices, prune_missing=True)
    if settings.scenes_config_path.exists():
        memory.replace_scenes(scenes)
    if settings.automations_config_path.exists():
        memory.replace_automations(automations)

    profile_values = {
        "assistant_name": assistant_doc.get("name", settings.app_name),
        "assistant_language": assistant_doc.get("language", settings.default_language),
        "assistant_city": assistant_doc.get("home_city", settings.default_home_city),
        "assistant_wake_word": voice_doc.get("wake_word", settings.default_wake_word),
        "name": profile_doc.get("name", settings.default_profile_name),
        "language": profile_doc.get("preferred_language", settings.default_language),
        "timezone": profile_doc.get("timezone", "UTC"),
        "preferences": profile_doc.get("preferences", {}),
    }

    for key, value in profile_values.items():
        if isinstance(value, dict):
            memory.upsert_user_profile(key, value)
        else:
            memory.upsert_user_profile(key, {"value": value})

    if settings.use_sample_seed_data and not memory.list_rooms():
        memory.seed_sample_data()

    return {
        "assistant_path": str(settings.assistant_config_path),
        "profile_path": str(settings.profile_config_path),
        "rooms_path": str(settings.rooms_config_path),
        "devices_path": str(settings.devices_config_path),
        "scenes_path": str(settings.scenes_config_path),
        "automations_path": str(settings.automations_config_path),
        "room_count": len(rooms),
        "device_count": len(devices),
        "scene_count": len(scenes),
        "automation_count": len(automations),
        "assistant_name": assistant_doc.get("name", settings.app_name),
        "voice": {
            "wake_word": voice_doc.get("wake_word", settings.default_wake_word),
            "enabled": voice_doc.get("enabled", settings.enable_voice_blueprint),
        },
        "storage": storage_doc or {"database": "sqlite", "vector_store": "chroma", "local_only": True},
    }
