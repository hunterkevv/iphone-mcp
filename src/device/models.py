from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class DeviceInfo:
    model: str
    ios_version: str
    battery_level: Optional[int]
    device_name: str
    udid: str


@dataclass(slots=True)
class AppInfo:
    bundle_id: str
    name: str
    version: str
    is_system_app: bool
