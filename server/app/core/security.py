from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4


class ActionConfirmationManager:
    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds
        self._pending: dict[str, dict] = {}

    def authorize(self, tool_name: str, payload: dict, token: str | None) -> bool:
        self._purge_expired()
        if not token or token not in self._pending:
            return False
        record = self._pending[token]
        payload_hash = self._payload_hash(payload)
        if record["tool_name"] != tool_name or record["payload_hash"] != payload_hash:
            return False
        del self._pending[token]
        return True

    def issue(self, tool_name: str, payload: dict) -> str:
        self._purge_expired()
        token = uuid4().hex
        self._pending[token] = {
            "tool_name": tool_name,
            "payload_hash": self._payload_hash(payload),
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=self.window_seconds),
        }
        return token

    @staticmethod
    def _payload_hash(payload: dict) -> str:
        serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _purge_expired(self) -> None:
        now = datetime.now(timezone.utc)
        expired = [token for token, record in self._pending.items() if record["expires_at"] <= now]
        for token in expired:
            del self._pending[token]


class ToolPermissionGuard:
    def __init__(self, confirmation_manager: ActionConfirmationManager):
        self.confirmation_manager = confirmation_manager

    def authorize(self, *, tool_name: str, critical: bool, payload: dict, confirmation_token: str | None) -> dict:
        if not critical:
            return {"allowed": True}

        if self.confirmation_manager.authorize(tool_name, payload, confirmation_token):
            return {"allowed": True}

        token = self.confirmation_manager.issue(tool_name, payload)
        return {
            "allowed": False,
            "message": f"Tool '{tool_name}' vereist expliciete bevestiging voordat deze wordt uitgevoerd.",
            "requires_confirmation": True,
            "confirmation_token": token,
        }


def reject_generated_code_execution(_: str) -> None:
    raise PermissionError("Tukkie voert geen onbekende of gegenereerde code direct uit.")
