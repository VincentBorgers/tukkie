from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field


class ReasoningDecision(BaseModel):
    intent: str = "chat"
    tool_name: str | None = None
    tool_args: dict[str, Any] = Field(default_factory=dict)
    explanation: str = ""


class DutchReasoningEngine:
    def decide(self, message: str, knowledge_bundle) -> ReasoningDecision:
        text = message.lower()
        devices = knowledge_bundle.devices
        scenes = knowledge_bundle.scenes

        if any(word in text for word in ["camera", "oprit", "beveiliging"]) and "status" in text:
            device = self._match_device(text, devices, allowed_types={"camera"})
            return ReasoningDecision(
                intent="inspect_camera",
                tool_name="camera_status",
                tool_args={"device_id": device["id"] if device else None},
                explanation="Camerastatus gevraagd.",
            )

        if any(word in text for word in ["deurbel", "intercom", "ring"]):
            device = self._match_device(text, devices, allowed_types={"doorbell", "intercom"})
            return ReasoningDecision(
                intent="inspect_doorbell",
                tool_name="doorbell_status",
                tool_args={"device_id": device["id"] if device else None},
                explanation="Deurbel- of intercomstatus gevraagd.",
            )

        if "netwerk" in text or "wifi" in text:
            return ReasoningDecision(
                intent="network_summary",
                tool_name="network_monitor",
                tool_args={"include_anomaly_detection": True},
                explanation="Netwerkstatus gevraagd.",
            )

        if "energie" in text or "verbruik" in text:
            room = self._match_room(text, knowledge_bundle.rooms)
            return ReasoningDecision(
                intent="energy_summary",
                tool_name="energy_usage",
                tool_args={"room_id": room["id"] if room else None, "window": "24h"},
                explanation="Energieverbruik gevraagd.",
            )

        if any(word in text for word in ["temperatuur", "thermostaat", "verwarming"]):
            device = self._match_device(text, devices, allowed_types={"thermostat"})
            temperature = self._extract_temperature(text)
            if device and temperature is not None:
                return ReasoningDecision(
                    intent="set_temperature",
                    tool_name="temperature_control",
                    tool_args={"device_id": device["id"], "target_celsius": temperature},
                    explanation="Temperatuurwijziging gevraagd.",
                )

        if "scene" in text or "movie mode" in text or "filmstand" in text:
            scene = self._match_scene(text, scenes)
            if scene:
                return ReasoningDecision(
                    intent="activate_scene",
                    tool_name="scene_activate",
                    tool_args={"scene_id": scene["id"]},
                    explanation="Bekende scene gevraagd.",
                )

        if any(word in text for word in ["licht", "lamp", "verlichting"]):
            device = self._match_device(text, devices, allowed_types={"light"})
            action = self._extract_light_action(text)
            if device and action:
                payload = {"device_id": device["id"], "action": action}
                brightness = self._extract_brightness(text)
                if brightness is not None:
                    payload["brightness"] = brightness
                return ReasoningDecision(
                    intent="control_light",
                    tool_name="lights_control",
                    tool_args=payload,
                    explanation="Lichtactie herkend.",
                )

        if any(word in text for word in ["automatiseer", "automatisering", "routine"]) and "maak" in text:
            return ReasoningDecision(
                intent="create_automation",
                tool_name="automation_create",
                tool_args={
                    "name": "Nieuwe routine",
                    "trigger_description": "Terugkerend gedrag uit chatopdracht",
                    "action_description": message,
                },
                explanation="Automatiseringsverzoek herkend.",
            )

        return ReasoningDecision(intent="chat", explanation="Geen tool nodig.")

    @staticmethod
    def _match_device(text: str, devices: list[dict[str, Any]], allowed_types: set[str] | None = None) -> dict[str, Any] | None:
        for device in devices:
            if allowed_types and device["type"] not in allowed_types:
                continue
            name_tokens = {token for token in re.split(r"[\s_-]+", device["name"].lower()) if token}
            if any(token in text for token in name_tokens):
                return device
        for device in devices:
            if allowed_types and device["type"] not in allowed_types:
                continue
            return device
        return None

    @staticmethod
    def _match_room(text: str, rooms: list[dict[str, Any]]) -> dict[str, Any] | None:
        for room in rooms:
            if room["name"].lower() in text:
                return room
        return None

    @staticmethod
    def _match_scene(text: str, scenes: list[dict[str, Any]]) -> dict[str, Any] | None:
        for scene in scenes:
            if scene["name"].lower() in text or scene["id"].replace("-", " ") in text:
                return scene
        return None

    @staticmethod
    def _extract_temperature(text: str) -> float | None:
        match = re.search(r"(\d{2}(?:[.,]\d)?)\s*gr", text)
        if match:
            return float(match.group(1).replace(",", "."))
        match = re.search(r"(\d{2}(?:[.,]\d)?)", text)
        if match:
            return float(match.group(1).replace(",", "."))
        return None

    @staticmethod
    def _extract_brightness(text: str) -> int | None:
        match = re.search(r"(\d{1,3})\s*%", text)
        if match:
            return max(1, min(100, int(match.group(1))))
        return None

    @staticmethod
    def _extract_light_action(text: str) -> str | None:
        if "uit" in text:
            return "off"
        if "dim" in text or "%" in text:
            return "brightness"
        if "aan" in text:
            return "on"
        return None
