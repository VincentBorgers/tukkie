from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import (
    AutomationRule,
    AutomationSuggestion,
    ChatMessage,
    DeviceState,
    InteractionEvent,
    LongTermMemory,
    NetworkSnapshot,
    RoomState,
    SceneState,
    utc_now,
)


class MemoryStore:
    def __init__(self, db_path: Path, cipher: Any | None = None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.cipher = cipher

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _dump(value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _load(value: str | None, default: Any) -> Any:
        if not value:
            return default
        return json.loads(value)

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS long_term_memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance REAL NOT NULL,
                    tags_json TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS rooms (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    purpose TEXT,
                    status TEXT,
                    metrics_json TEXT
                );

                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    room TEXT NOT NULL,
                    type TEXT NOT NULL,
                    vendor TEXT,
                    integration TEXT,
                    status TEXT,
                    state_json TEXT,
                    capabilities_json TEXT,
                    metadata_json TEXT
                );

                CREATE TABLE IF NOT EXISTS scenes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    room TEXT NOT NULL,
                    state_json TEXT,
                    metadata_json TEXT
                );

                CREATE TABLE IF NOT EXISTS automation_rules (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    trigger_json TEXT NOT NULL,
                    action_json TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    metadata_json TEXT
                );

                CREATE TABLE IF NOT EXISTS interaction_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    room TEXT,
                    device_id TEXT,
                    action TEXT NOT NULL,
                    payload_json TEXT
                );

                CREATE TABLE IF NOT EXISTS suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    status TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS network_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    devices_json TEXT,
                    traffic_json TEXT,
                    anomaly_score REAL NOT NULL,
                    summary TEXT NOT NULL
                );
                """
            )

    def seed_sample_data(self) -> None:
        if self.list_rooms():
            return

        rooms = [
            RoomState(id="living-room", name="Woonkamer", purpose="ontspanning", metrics={"temperature": 21.5}),
            RoomState(id="kitchen", name="Keuken", purpose="koken", metrics={"temperature": 20.4}),
            RoomState(id="bedroom", name="Slaapkamer", purpose="rust", metrics={"temperature": 19.1}),
            RoomState(id="hallway", name="Hal", purpose="toegang", metrics={"temperature": 18.7}),
            RoomState(id="outside", name="Buiten", purpose="beveiliging", metrics={"temperature": 9.2}),
        ]
        for room in rooms:
            self.add_room(room)

        devices = [
            DeviceState(
                id="livingroom-main-light",
                name="Woonkamer hoofdlicht",
                room="living-room",
                type="light",
                vendor="tuya",
                integration="tuya",
                status="online",
                state={"power": "off", "brightness": 45},
                capabilities=["power", "brightness"],
            ),
            DeviceState(
                id="movie-scene-lightstrip",
                name="TV lightstrip",
                room="living-room",
                type="light",
                vendor="tuya",
                integration="tuya",
                status="online",
                state={"power": "on", "brightness": 20},
                capabilities=["power", "brightness"],
            ),
            DeviceState(
                id="front-door-ring",
                name="Voordeur bel",
                room="hallway",
                type="doorbell",
                vendor="ring",
                integration="ring",
                status="online",
                state={"last_ring": "geen activiteit", "battery": 84},
                capabilities=["status", "battery"],
            ),
            DeviceState(
                id="hallway-intercom",
                name="Hal intercom",
                room="hallway",
                type="intercom",
                vendor="ring",
                integration="ring",
                status="online",
                state={"mode": "standby"},
                capabilities=["status"],
            ),
            DeviceState(
                id="driveway-camera",
                name="Oprit camera",
                room="outside",
                type="camera",
                vendor="imou",
                integration="imou",
                status="online",
                state={"recording": True, "last_alert": "Geen meldingen"},
                capabilities=["status", "alerts", "local_feed"],
            ),
            DeviceState(
                id="thermostat-living-room",
                name="Woonkamer thermostaat",
                room="living-room",
                type="thermostat",
                vendor="generic",
                integration="generic",
                status="online",
                state={"target_celsius": 21.0},
                capabilities=["target_celsius"],
            ),
        ]
        for device in devices:
            self.add_device(device)

        scenes = [
            SceneState(
                id="movie-mode",
                name="Movie Mode",
                room="living-room",
                state={"lights": "dim", "brightness": 15},
                metadata={"description": "Dimt de woonkamer voor filmavond"},
            ),
            SceneState(
                id="night-security",
                name="Nachtbeveiliging",
                room="outside",
                state={"camera_alerts": "hoog"},
                metadata={"description": "Verhoogt camera alert-niveau"},
            ),
        ]
        for scene in scenes:
            self.add_scene(scene)

        self.upsert_user_profile("name", {"value": "Household"})
        self.upsert_user_profile("language", {"value": "nl-NL"})
        self.upsert_user_profile("assistant_name", {"value": "Tukkie"})
        self.upsert_user_profile("assistant_wake_word", {"value": "tukkie"})
        self.upsert_suggestion(
            AutomationSuggestion(
                title="Automatiseer avondscène",
                description="Ik zie dat de woonkamerverlichting vaak in de avond wordt gedimd. Wil je een automatische avondroutine rond 20:30?",
                confidence=0.74,
                metadata={"kind": "routine", "scene_id": "movie-mode"},
            )
        )

    def append_message(self, message: ChatMessage) -> ChatMessage:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO conversations(session_id, role, content, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    message.session_id,
                    message.role,
                    message.content,
                    self._dump(message.metadata),
                    message.created_at,
                ),
            )
            message.id = cursor.lastrowid
            return message

    def get_conversation(self, session_id: str, limit: int = 12) -> list[ChatMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM conversations
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        return [
            ChatMessage(
                id=row["id"],
                session_id=row["session_id"],
                role=row["role"],
                content=row["content"],
                metadata=self._load(row["metadata_json"], {}),
                created_at=row["created_at"],
            )
            for row in reversed(rows)
        ]

    def save_long_term_memory(self, record: LongTermMemory) -> LongTermMemory:
        encrypted_content = self.cipher.encrypt(record.content) if self.cipher else record.content
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO long_term_memories(category, title, content, importance, tags_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.category,
                    record.title,
                    encrypted_content,
                    record.importance,
                    self._dump(record.tags),
                    record.created_at,
                    record.updated_at,
                ),
            )
            record.id = cursor.lastrowid
            return record

    def search_long_term_memory(self, query: str, limit: int = 5) -> list[LongTermMemory]:
        pattern = f"%{query.lower()}%"
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM long_term_memories
                WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?
                ORDER BY importance DESC, updated_at DESC
                LIMIT ?
                """,
                (pattern, pattern, limit),
            ).fetchall()
        results: list[LongTermMemory] = []
        for row in rows:
            content = row["content"]
            if self.cipher:
                content = self.cipher.decrypt(content)
            results.append(
                LongTermMemory(
                    id=row["id"],
                    category=row["category"],
                    title=row["title"],
                    content=content,
                    importance=row["importance"],
                    tags=self._load(row["tags_json"], []),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return results

    def upsert_user_profile(self, key: str, value: dict[str, Any], updated_at: str | None = None) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO user_profile(key, value_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value_json = excluded.value_json,
                    updated_at = excluded.updated_at
                """,
                (key, self._dump(value), updated_at or utc_now()),
            )

    def get_user_profile(self) -> dict[str, Any]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM user_profile ORDER BY key").fetchall()
        return {row["key"]: self._load(row["value_json"], {}) for row in rows}

    def add_room(self, room: RoomState) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO rooms(id, name, purpose, status, metrics_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    purpose = excluded.purpose,
                    status = excluded.status,
                    metrics_json = excluded.metrics_json
                """,
                (room.id, room.name, room.purpose, room.status, self._dump(room.metrics)),
            )

    def replace_rooms(self, rooms: list[RoomState]) -> None:
        room_ids = [room.id for room in rooms]
        with self._connect() as connection:
            if room_ids:
                placeholders = ", ".join("?" for _ in room_ids)
                connection.execute(f"DELETE FROM rooms WHERE id NOT IN ({placeholders})", room_ids)
            else:
                connection.execute("DELETE FROM rooms")
        for room in rooms:
            self.add_room(room)

    def list_rooms(self) -> list[RoomState]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM rooms ORDER BY name").fetchall()
        return [
            RoomState(
                id=row["id"],
                name=row["name"],
                purpose=row["purpose"] or "",
                status=row["status"] or "unknown",
                metrics=self._load(row["metrics_json"], {}),
            )
            for row in rows
        ]

    def add_device(self, device: DeviceState) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO devices(id, name, room, type, vendor, integration, status, state_json, capabilities_json, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    room = excluded.room,
                    type = excluded.type,
                    vendor = excluded.vendor,
                    integration = excluded.integration,
                    status = excluded.status,
                    state_json = excluded.state_json,
                    capabilities_json = excluded.capabilities_json,
                    metadata_json = excluded.metadata_json
                """,
                (
                    device.id,
                    device.name,
                    device.room,
                    device.type,
                    device.vendor,
                    device.integration,
                    device.status,
                    self._dump(device.state),
                    self._dump(device.capabilities),
                    self._dump(device.metadata),
                ),
            )

    def sync_devices_from_config(self, devices: list[DeviceState], prune_missing: bool = True) -> None:
        device_ids = [device.id for device in devices]
        if prune_missing:
            with self._connect() as connection:
                if device_ids:
                    placeholders = ", ".join("?" for _ in device_ids)
                    connection.execute(f"DELETE FROM devices WHERE id NOT IN ({placeholders})", device_ids)
                else:
                    connection.execute("DELETE FROM devices")

        for configured_device in devices:
            existing = self.get_device(configured_device.id)
            if existing:
                merged_state = dict(existing.state)
                merged_state.update(configured_device.state)
                merged_capabilities = sorted(set(existing.capabilities) | set(configured_device.capabilities))
                merged_metadata = dict(existing.metadata)
                merged_metadata.update(configured_device.metadata)
                configured_device.state = merged_state
                configured_device.capabilities = merged_capabilities
                configured_device.metadata = merged_metadata
                if configured_device.status in {"configured", "unknown"} and existing.status not in {"configured", "unknown"}:
                    configured_device.status = existing.status
            self.add_device(configured_device)

    def update_device_state(self, device_id: str, state_patch: dict[str, Any], status: str | None = None) -> DeviceState | None:
        device = self.get_device(device_id)
        if not device:
            return None
        device.state.update(state_patch)
        if status:
            device.status = status
        self.add_device(device)
        return device

    def get_device(self, device_id: str) -> DeviceState | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
        if row is None:
            return None
        return DeviceState(
            id=row["id"],
            name=row["name"],
            room=row["room"],
            type=row["type"],
            vendor=row["vendor"] or "generic",
            integration=row["integration"] or "generic",
            status=row["status"] or "unknown",
            state=self._load(row["state_json"], {}),
            capabilities=self._load(row["capabilities_json"], []),
            metadata=self._load(row["metadata_json"], {}),
        )

    def list_devices(self, room_id: str | None = None) -> list[DeviceState]:
        query = "SELECT * FROM devices"
        params: tuple[Any, ...] = ()
        if room_id:
            query += " WHERE room = ?"
            params = (room_id,)
        query += " ORDER BY name"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            DeviceState(
                id=row["id"],
                name=row["name"],
                room=row["room"],
                type=row["type"],
                vendor=row["vendor"] or "generic",
                integration=row["integration"] or "generic",
                status=row["status"] or "unknown",
                state=self._load(row["state_json"], {}),
                capabilities=self._load(row["capabilities_json"], []),
                metadata=self._load(row["metadata_json"], {}),
            )
            for row in rows
        ]

    def add_scene(self, scene: SceneState) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO scenes(id, name, room, state_json, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    room = excluded.room,
                    state_json = excluded.state_json,
                    metadata_json = excluded.metadata_json
                """,
                (scene.id, scene.name, scene.room, self._dump(scene.state), self._dump(scene.metadata)),
            )

    def replace_scenes(self, scenes: list[SceneState]) -> None:
        scene_ids = [scene.id for scene in scenes]
        with self._connect() as connection:
            if scene_ids:
                placeholders = ", ".join("?" for _ in scene_ids)
                connection.execute(f"DELETE FROM scenes WHERE id NOT IN ({placeholders})", scene_ids)
            else:
                connection.execute("DELETE FROM scenes")
        for scene in scenes:
            self.add_scene(scene)

    def list_scenes(self) -> list[SceneState]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM scenes ORDER BY name").fetchall()
        return [
            SceneState(
                id=row["id"],
                name=row["name"],
                room=row["room"],
                state=self._load(row["state_json"], {}),
                metadata=self._load(row["metadata_json"], {}),
            )
            for row in rows
        ]

    def upsert_automation(self, rule: AutomationRule) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO automation_rules(id, name, description, trigger_json, action_json, enabled, confidence, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    description = excluded.description,
                    trigger_json = excluded.trigger_json,
                    action_json = excluded.action_json,
                    enabled = excluded.enabled,
                    confidence = excluded.confidence,
                    metadata_json = excluded.metadata_json
                """,
                (
                    rule.id,
                    rule.name,
                    rule.description,
                    self._dump(rule.trigger),
                    self._dump(rule.action),
                    int(rule.enabled),
                    rule.confidence,
                    self._dump(rule.metadata),
                ),
            )

    def replace_automations(self, automations: list[AutomationRule]) -> None:
        automation_ids = [automation.id for automation in automations]
        with self._connect() as connection:
            if automation_ids:
                placeholders = ", ".join("?" for _ in automation_ids)
                connection.execute(
                    f"DELETE FROM automation_rules WHERE id NOT IN ({placeholders})",
                    automation_ids,
                )
            else:
                connection.execute("DELETE FROM automation_rules")
        for automation in automations:
            self.upsert_automation(automation)

    def list_automations(self) -> list[AutomationRule]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM automation_rules ORDER BY name").fetchall()
        return [
            AutomationRule(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                trigger=self._load(row["trigger_json"], {}),
                action=self._load(row["action_json"], {}),
                enabled=bool(row["enabled"]),
                confidence=row["confidence"],
                metadata=self._load(row["metadata_json"], {}),
            )
            for row in rows
        ]

    def record_interaction(self, event: InteractionEvent) -> InteractionEvent:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO interaction_events(event_type, timestamp, room, device_id, action, payload_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_type,
                    event.timestamp,
                    event.room,
                    event.device_id,
                    event.action,
                    self._dump(event.payload),
                ),
            )
            event.id = cursor.lastrowid
            return event

    def get_recent_interactions(self, limit: int = 100) -> list[InteractionEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM interaction_events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            InteractionEvent(
                id=row["id"],
                event_type=row["event_type"],
                timestamp=row["timestamp"],
                room=row["room"],
                device_id=row["device_id"],
                action=row["action"],
                payload=self._load(row["payload_json"], {}),
            )
            for row in reversed(rows)
        ]

    def get_recent_activity(self, limit: int = 20) -> list[dict[str, Any]]:
        events = self.get_recent_interactions(limit=limit)
        activity: list[dict[str, Any]] = []
        for event in reversed(events):
            device_name = None
            if event.device_id:
                device = self.get_device(event.device_id)
                device_name = device.name if device else event.device_id
            activity.append(
                {
                    "id": event.id,
                    "timestamp": event.timestamp,
                    "event_type": event.event_type,
                    "action": event.action,
                    "room": event.room,
                    "device_id": event.device_id,
                    "device_name": device_name,
                    "payload": event.payload,
                }
            )
        return activity

    def upsert_suggestion(self, suggestion: AutomationSuggestion) -> None:
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT id FROM suggestions WHERE title = ? AND status = ?",
                (suggestion.title, suggestion.status),
            ).fetchone()
            if existing:
                connection.execute(
                    """
                    UPDATE suggestions
                    SET description = ?, confidence = ?, metadata_json = ?, created_at = ?
                    WHERE id = ?
                    """,
                    (
                        suggestion.description,
                        suggestion.confidence,
                        self._dump(suggestion.metadata),
                        suggestion.created_at,
                        existing["id"],
                    ),
                )
                return

            connection.execute(
                """
                INSERT INTO suggestions(title, description, confidence, status, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    suggestion.title,
                    suggestion.description,
                    suggestion.confidence,
                    suggestion.status,
                    self._dump(suggestion.metadata),
                    suggestion.created_at,
                ),
            )

    def list_suggestions(self, status: str = "open", limit: int = 10) -> list[AutomationSuggestion]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM suggestions
                WHERE status = ?
                ORDER BY confidence DESC, created_at DESC
                LIMIT ?
                """,
                (status, limit),
            ).fetchall()
        return [
            AutomationSuggestion(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                confidence=row["confidence"],
                status=row["status"],
                metadata=self._load(row["metadata_json"], {}),
                created_at=row["created_at"],
            )
            for row in rows
        ]

    def save_network_snapshot(self, snapshot: NetworkSnapshot) -> NetworkSnapshot:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO network_snapshots(created_at, devices_json, traffic_json, anomaly_score, summary)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    snapshot.created_at,
                    self._dump(snapshot.devices),
                    self._dump(snapshot.traffic),
                    snapshot.anomaly_score,
                    snapshot.summary,
                ),
            )
            snapshot.id = cursor.lastrowid
            return snapshot

    def latest_network_snapshot(self) -> NetworkSnapshot | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM network_snapshots ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if row is None:
            return None
        return NetworkSnapshot(
            id=row["id"],
            created_at=row["created_at"],
            devices=self._load(row["devices_json"], []),
            traffic=self._load(row["traffic_json"], {}),
            anomaly_score=row["anomaly_score"],
            summary=row["summary"],
        )

    def get_overview(self) -> dict[str, Any]:
        rooms = self.list_rooms()
        devices = self.list_devices()
        suggestions = self.list_suggestions()
        network_snapshot = self.latest_network_snapshot()
        return {
            "rooms": [room.model_dump() for room in rooms],
            "devices": [device.model_dump() for device in devices],
            "scenes": [scene.model_dump() for scene in self.list_scenes()],
            "automations": [automation.model_dump() for automation in self.list_automations()],
            "suggestions": [suggestion.model_dump() for suggestion in suggestions],
            "network": network_snapshot.model_dump() if network_snapshot else None,
            "profile": self.get_user_profile(),
        }
