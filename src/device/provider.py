from __future__ import annotations

import asyncio
from typing import List

from .client import PyMobileDevice3Client
from .models import DeviceInfo, AppInfo


class DeviceInfoProvider:
    def __init__(self, udid: str):
        self.client = PyMobileDevice3Client(udid)

    async def get_device_info(self) -> DeviceInfo:
        return await asyncio.to_thread(self.client.get_device_info_sync)

    async def list_installed_apps(self) -> List[AppInfo]:
        return await asyncio.to_thread(self.client.list_installed_apps_sync)
