from __future__ import annotations

import asyncio
from typing import List
from loguru import logger

from ..utils import DeviceNotFoundError
from .models import DeviceInfo, AppInfo
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.usbmux import list_devices
from pymobiledevice3.services.installation_proxy import InstallationProxyService as MobileInstallationProxyService


class PyMobileDevice3Client:
    def __init__(self, udid: str):
        self.udid = udid

    def _get_lockdown_client(self):
        devices = list_devices()
        target_device = None
        for device in devices:
            if hasattr(device, 'serial') and device.serial == self.udid:
                target_device = device
                break
        if target_device is None:
            raise DeviceNotFoundError(f"Device with UDID {self.udid} not found")
        return create_using_usbmux(serial=target_device.serial)

    def get_device_info_sync(self) -> DeviceInfo:
        client = self._get_lockdown_client()
        info = client.all_values

        if not isinstance(info, dict):
            raise DeviceNotFoundError("Unexpected lockdown data structure")

        battery = info.get("BatteryCurrentCapacity")
        return DeviceInfo(
            model=str(info.get("ProductType", "Unknown")),
            ios_version=str(info.get("ProductVersion", "Unknown")),
            battery_level=battery if isinstance(battery, int) else None,
            device_name=str(info.get("DeviceName", "Unknown")),
            udid=str(info.get("UniqueDeviceID", self.udid)),
        )

    def list_installed_apps_sync(self) -> List[AppInfo]:
        client = self._get_lockdown_client()

        with MobileInstallationProxyService(client) as mip:
            apps = mip.lookup()
            results: List[AppInfo] = []
            for bundle_id, meta in apps.items():
                try:
                    results.append(
                        AppInfo(
                            bundle_id=bundle_id,
                            name=str(meta.get("CFBundleDisplayName") or meta.get("CFBundleName") or bundle_id),
                            version=str(meta.get("CFBundleShortVersionString", "")),
                            is_system_app=bool(meta.get("ApplicationType") == "System"),
                        )
                    )
                except Exception:
                    continue
            return results
