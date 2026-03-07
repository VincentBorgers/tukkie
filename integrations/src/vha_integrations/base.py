from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DeviceAdapter(ABC):
    name: str = "generic"

    def __init__(self, allow_fallback: bool = True):
        self.allow_fallback = allow_fallback

    @abstractmethod
    def health(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def get_status(self, device: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    def execute_action(self, device: dict[str, Any], action: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    def fetch_snapshot(self, device: dict[str, Any]) -> tuple[bytes, str] | None:
        return None


class GenericDeviceAdapter(DeviceAdapter):
    name = "generic"

    def health(self) -> dict[str, Any]:
        return {
            "adapter": self.name,
            "connected": True,
            "available": True,
            "mode": "local-cache" if self.allow_fallback else "configured-only",
        }

    def get_status(self, device: dict[str, Any]) -> dict[str, Any]:
        return {
            "device_id": device["id"],
            "status": device.get("status", "unknown"),
            "state": device.get("state", {}),
            "source": "local-cache",
        }

    def execute_action(self, device: dict[str, Any], action: str, payload: dict[str, Any]) -> dict[str, Any]:
        state = dict(device.get("state", {}))
        if action in {"on", "off"}:
            state["power"] = action
        state.update(payload)
        return {
            "device_id": device["id"],
            "status": "ok",
            "state": state,
            "message": f"Actie {action} lokaal voorbereid via generieke adapter.",
        }
