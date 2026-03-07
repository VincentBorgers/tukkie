from __future__ import annotations

from .base import DeviceAdapter


class RingAdapter(DeviceAdapter):
    name = "ring"

    def health(self) -> dict[str, str | bool]:
        return {
            "adapter": self.name,
            "connected": False,
            "available": True,
            "mode": "cloud-credentials-required",
        }

    def get_status(self, device: dict) -> dict:
        return {
            "device_id": device["id"],
            "status": device.get("status", "configured"),
            "state": device.get("state", {}),
            "alerts": device.get("state", {}).get("last_ring", "geen activiteit"),
            "source": "configured-cache",
        }

    def execute_action(self, device: dict, action: str, payload: dict) -> dict:
        return {
            "device_id": device["id"],
            "status": "ok",
            "state": device.get("state", {}),
            "message": f"Ring actie '{action}' is als veilige template geregistreerd, maar voert standaard niets destructiefs uit.",
        }
