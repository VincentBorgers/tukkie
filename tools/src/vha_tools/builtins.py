from __future__ import annotations

from uuid import uuid4

from vha_memory.models import AutomationRule, InteractionEvent, NetworkSnapshot

from .base import ToolContext, ToolDefinition, ToolResult
from .schemas import (
    AutomationCreateInput,
    CameraStatusInput,
    DoorbellStatusInput,
    EnergyUsageInput,
    LightsControlInput,
    NetworkMonitorInput,
    SceneActivateInput,
    TemperatureControlInput,
)


def _record_tool_event(context: ToolContext, *, action: str, room: str | None, device_id: str | None, payload: dict) -> None:
    context.memory.record_interaction(
        InteractionEvent(
            event_type="tool_execution",
            room=room,
            device_id=device_id,
            action=action,
            payload=payload,
        )
    )


def _lights_control(payload: LightsControlInput, context: ToolContext) -> ToolResult:
    device = context.memory.get_device(payload.device_id)
    if device is None:
        return ToolResult(ok=False, message="Lichtapparaat niet gevonden.")

    action_payload = {}
    if payload.action == "brightness":
        action_payload["brightness"] = payload.brightness
    elif payload.action == "toggle":
        current = device.state.get("power", "off")
        action_payload["power"] = "off" if current == "on" else "on"
    else:
        action_payload["power"] = payload.action
        if payload.brightness is not None:
            action_payload["brightness"] = payload.brightness

    result = context.integrations.execute_device_action(device.model_dump(), payload.action, action_payload)
    updated_state = result.get("state", {})
    updated_device = context.memory.update_device_state(device.id, updated_state, status="online")
    _record_tool_event(context, action=f"lights:{payload.action}", room=device.room, device_id=device.id, payload=action_payload)

    return ToolResult(
        ok=True,
        message=f"{device.name} bijgewerkt.",
        data={"device": updated_device.model_dump() if updated_device else device.model_dump(), "result": result},
    )


def _camera_status(payload: CameraStatusInput, context: ToolContext) -> ToolResult:
    devices = context.memory.list_devices()
    cameras = [device for device in devices if device.type == "camera"]
    if payload.device_id:
        cameras = [device for device in cameras if device.id == payload.device_id]

    statuses = [context.integrations.get_device_status(camera.model_dump()) for camera in cameras]
    return ToolResult(ok=True, message="Camerastatus opgehaald.", data={"cameras": statuses})


def _doorbell_status(payload: DoorbellStatusInput, context: ToolContext) -> ToolResult:
    devices = context.memory.list_devices()
    doorbells = [device for device in devices if device.type in {"doorbell", "intercom"}]
    if payload.device_id:
        doorbells = [device for device in doorbells if device.id == payload.device_id]

    statuses = [context.integrations.get_device_status(device.model_dump()) for device in doorbells]
    return ToolResult(ok=True, message="Deurbel- en intercomstatus opgehaald.", data={"devices": statuses})


def _temperature_control(payload: TemperatureControlInput, context: ToolContext) -> ToolResult:
    device = context.memory.get_device(payload.device_id)
    if device is None:
        return ToolResult(ok=False, message="Thermostaat niet gevonden.")

    result = context.integrations.execute_device_action(
        device.model_dump(),
        "set_temperature",
        {"target_celsius": payload.target_celsius},
    )
    updated_device = context.memory.update_device_state(
        device.id,
        {"target_celsius": payload.target_celsius},
        status="online",
    )
    _record_tool_event(
        context,
        action="temperature:set",
        room=device.room,
        device_id=device.id,
        payload={"target_celsius": payload.target_celsius},
    )
    return ToolResult(
        ok=True,
        message=f"Temperatuur voor {device.name} ingesteld op {payload.target_celsius:.1f}°C.",
        data={"device": updated_device.model_dump() if updated_device else device.model_dump(), "result": result},
    )


def _energy_usage(payload: EnergyUsageInput, context: ToolContext) -> ToolResult:
    devices = context.memory.list_devices(room_id=payload.room_id)
    base_load = max(len(devices), 1) * 52
    active_devices = sum(1 for device in devices if device.state.get("power") == "on" or device.type == "camera")
    watts = base_load + active_devices * 37
    return ToolResult(
        ok=True,
        message="Energie-inschatting lokaal berekend.",
        data={
            "window": payload.window,
            "room_id": payload.room_id,
            "estimated_watts": watts,
            "active_devices": active_devices,
            "device_count": len(devices),
        },
    )


def _network_monitor(payload: NetworkMonitorInput, context: ToolContext) -> ToolResult:
    snapshot_data = context.integrations.network.snapshot()
    snapshot = context.memory.save_network_snapshot(
        NetworkSnapshot(
            devices=snapshot_data["devices"],
            traffic=snapshot_data["traffic"],
            anomaly_score=snapshot_data["anomaly_score"],
            summary=snapshot_data["summary"],
        )
    )
    return ToolResult(ok=True, message="Netwerksnapshot opgeslagen.", data=snapshot.model_dump())


def _automation_create(payload: AutomationCreateInput, context: ToolContext) -> ToolResult:
    rule = AutomationRule(
        id=f"automation-{uuid4().hex[:10]}",
        name=payload.name,
        description=f"Automatisch gegenereerd: {payload.trigger_description} -> {payload.action_description}",
        trigger={"description": payload.trigger_description, "schedule": payload.schedule},
        action={"description": payload.action_description},
        confidence=0.72,
        metadata={"created_by": "tukkie"},
    )
    context.memory.upsert_automation(rule)
    _record_tool_event(
        context,
        action="automation:create",
        room=None,
        device_id=None,
        payload=rule.model_dump(),
    )
    return ToolResult(ok=True, message=f"Automatisering '{payload.name}' is opgeslagen.", data=rule.model_dump())


def _scene_activate(payload: SceneActivateInput, context: ToolContext) -> ToolResult:
    scene = next((scene for scene in context.memory.list_scenes() if scene.id == payload.scene_id), None)
    if scene is None:
        return ToolResult(ok=False, message="Scene niet gevonden.")

    affected_devices = []
    for device in context.memory.list_devices(room_id=scene.room):
        if device.type != "light":
            continue
        updated = context.memory.update_device_state(
            device.id,
            {"power": "on", "brightness": scene.state.get("brightness", 20)},
            status="online",
        )
        if updated:
            affected_devices.append(updated.model_dump())

    _record_tool_event(
        context,
        action="scene:activate",
        room=scene.room,
        device_id=None,
        payload={"scene_id": scene.id},
    )
    return ToolResult(
        ok=True,
        message=f"Scene '{scene.name}' voorbereid voor kamer {scene.room}.",
        data={"scene": scene.model_dump(), "affected_devices": affected_devices},
    )


def build_default_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="lights_control",
            description="Schakel lampen aan of uit en pas helderheid veilig aan.",
            schema_model=LightsControlInput,
            executor=_lights_control,
        ),
        ToolDefinition(
            name="camera_status",
            description="Lees de status van Imou camera's en lokale alerts uit.",
            schema_model=CameraStatusInput,
            executor=_camera_status,
        ),
        ToolDefinition(
            name="doorbell_status",
            description="Lees de status van Ring deurbel of intercom uit.",
            schema_model=DoorbellStatusInput,
            executor=_doorbell_status,
        ),
        ToolDefinition(
            name="temperature_control",
            description="Stel een veilige doeltemperatuur in via een gecontroleerde tool.",
            schema_model=TemperatureControlInput,
            executor=_temperature_control,
            critical=True,
        ),
        ToolDefinition(
            name="energy_usage",
            description="Bereken een lokale energie-inschatting per ruimte of woning.",
            schema_model=EnergyUsageInput,
            executor=_energy_usage,
        ),
        ToolDefinition(
            name="network_monitor",
            description="Maak een veilige netwerksnapshot met afwijkingsanalyse.",
            schema_model=NetworkMonitorInput,
            executor=_network_monitor,
        ),
        ToolDefinition(
            name="automation_create",
            description="Sla een nieuwe automatisering op na expliciete bevestiging.",
            schema_model=AutomationCreateInput,
            executor=_automation_create,
            critical=True,
        ),
        ToolDefinition(
            name="scene_activate",
            description="Activeer een bekende scene voor een ruimte.",
            schema_model=SceneActivateInput,
            executor=_scene_activate,
            critical=True,
        ),
    ]
