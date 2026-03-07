from __future__ import annotations

import base64

import httpx

from .base import DeviceAdapter


class ImouCameraAdapter(DeviceAdapter):
    name = "imou"

    def health(self) -> dict[str, str | bool]:
        return {
            "adapter": self.name,
            "connected": True,
            "available": True,
            "mode": "local-http-snapshot",
        }

    def get_status(self, device: dict) -> dict:
        state = device.get("state", {})
        metadata = device.get("metadata", {})
        snapshot_url = metadata.get("snapshot_url")
        reachable = False
        if snapshot_url:
            try:
                response = httpx.get(snapshot_url, headers=self._auth_headers(metadata), timeout=5.0)
                reachable = response.status_code == 200
            except httpx.HTTPError:
                reachable = False
        return {
            "device_id": device["id"],
            "status": "online" if reachable or not snapshot_url else "offline",
            "state": {
                "recording": state.get("recording", False),
                "last_alert": state.get("last_alert", "geen meldingen"),
                "reachable": reachable,
                "stream_url": metadata.get("stream_url", ""),
            },
            "recording": state.get("recording", False),
            "last_alert": state.get("last_alert", "geen meldingen"),
            "local_feed_url": f"/api/cameras/{device['id']}/snapshot",
            "source": "snapshot-proxy" if snapshot_url else "local-cache",
        }

    def execute_action(self, device: dict, action: str, payload: dict) -> dict:
        state = dict(device.get("state", {}))
        if action == "arm":
            state["recording"] = True
        if action == "disarm":
            state["recording"] = False
        return {
            "device_id": device["id"],
            "status": "ok",
            "state": state,
            "message": "Imou camera actie lokaal voorbereid.",
        }

    def fetch_snapshot(self, device: dict) -> tuple[bytes, str] | None:
        metadata = device.get("metadata", {})
        snapshot_url = metadata.get("snapshot_url")
        if not snapshot_url:
            return None

        response = httpx.get(snapshot_url, headers=self._auth_headers(metadata), timeout=8.0)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "image/jpeg")
        return response.content, content_type

    @staticmethod
    def _auth_headers(metadata: dict) -> dict[str, str]:
        username = metadata.get("username")
        password = metadata.get("password")
        if not username:
            return {}
        token = base64.b64encode(f"{username}:{password or ''}".encode("utf-8")).decode("utf-8")
        return {"Authorization": f"Basic {token}"}
