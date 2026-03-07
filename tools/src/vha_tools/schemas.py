from typing import Literal

from pydantic import BaseModel, Field


class LightsControlInput(BaseModel):
    device_id: str
    action: Literal["on", "off", "toggle", "brightness"]
    brightness: int | None = Field(default=None, ge=1, le=100)


class CameraStatusInput(BaseModel):
    device_id: str | None = None


class DoorbellStatusInput(BaseModel):
    device_id: str | None = None


class TemperatureControlInput(BaseModel):
    device_id: str
    target_celsius: float = Field(ge=10, le=30)


class EnergyUsageInput(BaseModel):
    room_id: str | None = None
    window: str = "24h"


class NetworkMonitorInput(BaseModel):
    include_anomaly_detection: bool = True


class AutomationCreateInput(BaseModel):
    name: str
    trigger_description: str
    action_description: str
    schedule: str | None = None


class SceneActivateInput(BaseModel):
    scene_id: str

