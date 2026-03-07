from __future__ import annotations

try:
    import tinytuya
except ImportError:  # pragma: no cover
    tinytuya = None

from .base import DeviceAdapter


class TuyaLightAdapter(DeviceAdapter):
    name = "tuya"

    def health(self) -> dict[str, str | bool]:
        return {
            "adapter": self.name,
            "connected": bool(tinytuya),
            "available": bool(tinytuya),
            "mode": "local-lan" if tinytuya else "package-missing",
        }

    def get_status(self, device: dict) -> dict:
        client = self._client(device)
        if client is not None:
            try:
                result = client.status() or {}
                dps = result.get("dps", {})
                power = dps.get(self._power_dps(device), dps.get("1"))
                brightness = dps.get(self._brightness_dps(device))
                return {
                    "device_id": device["id"],
                    "status": "online",
                    "state": {
                        "power": "on" if power in {True, "true", "True"} else "off",
                        "brightness": brightness,
                        "raw_dps": dps,
                    },
                    "vendor": "tuya",
                    "source": "tinytuya",
                }
            except Exception as exc:  # pragma: no cover
                return {
                    "device_id": device["id"],
                    "status": "error",
                    "state": device.get("state", {}),
                    "vendor": "tuya",
                    "error": str(exc),
                    "source": "tinytuya",
                }
        return {
            "device_id": device["id"],
            "status": device.get("status", "online"),
            "state": device.get("state", {}),
            "vendor": "tuya",
            "source": "local-cache",
        }

    def execute_action(self, device: dict, action: str, payload: dict) -> dict:
        next_state = dict(device.get("state", {}))
        client = self._client(device)
        if client is not None:
            try:
                if action == "on":
                    client.turn_on()
                elif action == "off":
                    client.turn_off()
                elif action == "brightness" and payload.get("brightness") is not None:
                    client.set_brightness_percentage(int(payload["brightness"]))
                status = self.get_status(device)
                next_state.update(status.get("state", {}))
                return {
                    "device_id": device["id"],
                    "status": "ok",
                    "state": next_state,
                    "message": "Tuya apparaat lokaal bijgewerkt.",
                }
            except Exception as exc:  # pragma: no cover
                return {
                    "device_id": device["id"],
                    "status": "error",
                    "state": next_state,
                    "message": f"Tuya actie mislukte: {exc}",
                }

        if action in {"on", "off"}:
            next_state["power"] = action
        if "brightness" in payload and payload["brightness"] is not None:
            next_state["brightness"] = payload["brightness"]
        return {
            "device_id": device["id"],
            "status": "ok",
            "state": next_state,
            "message": "Tuya fallback-opdracht verwerkt. Voeg lokale keys toe voor echte LAN-control.",
        }

    @staticmethod
    def _power_dps(device: dict) -> str:
        return str(device.get("metadata", {}).get("power_dps", "20"))

    @staticmethod
    def _brightness_dps(device: dict) -> str:
        return str(device.get("metadata", {}).get("brightness_dps", "22"))

    def _client(self, device: dict):
        if tinytuya is None:
            return None

        metadata = device.get("metadata", {})
        device_key = metadata.get("device_key")
        local_key = metadata.get("local_key")
        if not device_key or not local_key:
            return None

        address = metadata.get("address", "Auto")
        version = float(metadata.get("version", 3.3))
        device_kind = metadata.get("tuya_class", "bulb")

        if device_kind == "outlet":
            client = tinytuya.OutletDevice(device_key, address, local_key)
        else:
            client = tinytuya.BulbDevice(device_key, address, local_key)
        client.set_version(version)
        return client
