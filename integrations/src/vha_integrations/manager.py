from __future__ import annotations

from typing import Any

from .base import GenericDeviceAdapter
from .imou import ImouCameraAdapter
from .network import NetworkAnalyzer
from .ring import RingAdapter
from .tuya import TuyaLightAdapter


class IntegrationManager:
    def __init__(self, allow_fallback: bool = True):
        self.adapters = {
            "generic": GenericDeviceAdapter(allow_fallback=allow_fallback),
            "tuya": TuyaLightAdapter(allow_fallback=allow_fallback),
            "ring": RingAdapter(allow_fallback=allow_fallback),
            "imou": ImouCameraAdapter(allow_fallback=allow_fallback),
        }
        self.network = NetworkAnalyzer()

    def adapter_for(self, integration_name: str):
        return self.adapters.get(integration_name, self.adapters["generic"])

    def get_device_status(self, device: dict[str, Any]) -> dict[str, Any]:
        adapter = self.adapter_for(device.get("integration", "generic"))
        return adapter.get_status(device)

    def execute_device_action(self, device: dict[str, Any], action: str, payload: dict[str, Any]) -> dict[str, Any]:
        adapter = self.adapter_for(device.get("integration", "generic"))
        return adapter.execute_action(device, action, payload)

    def camera_snapshot(self, device: dict[str, Any]) -> tuple[bytes, str] | None:
        adapter = self.adapter_for(device.get("integration", "generic"))
        return adapter.fetch_snapshot(device)

    def health(self) -> list[dict[str, Any]]:
        return [adapter.health() for adapter in self.adapters.values()]
