from __future__ import annotations

import asyncio
import base64
import io
from typing import Any, Dict, List, Optional
from loguru import logger
from PIL import Image

from .device import DeviceInfoProvider, DeviceInfo, AppInfo
from .automation import XCUITestEngine, Element
from .utils import load_config
from .models import MCPError, MCPResponse
from mcp.types import ImageContent, TextContent


class MCPServer:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config if config is not None else load_config()
        udid = self.config.get("device", {}).get("udid")
        if not udid:
            raise ValueError("UDID is required")
        self.device_provider = DeviceInfoProvider(udid)
        self.engine = XCUITestEngine(self.config)
        self._methods: Dict[str, Any] = {}
        self._register_methods()

    def _register(self, name: str, func) -> None:
        self._methods[name] = func
        logger.debug("Registered method {}", name)

    def _register_methods(self) -> None:
        self._register("iphone_device_info", self.iphone_device_info)
        self._register("iphone_device_apps", self.iphone_device_apps)
        self._register("iphone_interface_snapshot", self.iphone_interface_snapshot)
        self._register("iphone_interface_elements", self.iphone_interface_elements)
        self._register("iphone_operate_click", self.iphone_operate_click)
        self._register("iphone_operate_swipe", self.iphone_operate_swipe)
        self._register("iphone_operate_text_input", self.iphone_operate_text_input)
        self._register("iphone_operate_app_launch", self.iphone_operate_app_launch)
        self._register("iphone_operate_get_current_bundle_id", self.iphone_operate_get_current_bundle_id)

    async def handle_call(self, method: str, **params) -> MCPResponse:
        if method not in self._methods:
            return MCPResponse(success=False, error=MCPError(code="method_not_found", message=method))
        try:
            result = await self._methods[method](**params)
            return MCPResponse(success=True, data=result)
        except Exception as e:
            logger.exception("Method {} failed", method)
            return MCPResponse(success=False, error=MCPError(code="internal_error", message=str(e)))

    async def iphone_device_info(self) -> Dict[str, Any]:
        info: DeviceInfo = await self.device_provider.get_device_info()
        return {'model': info.model, 'ios_version': info.ios_version, 'battery_level': info.battery_level, 'device_name': info.device_name, 'udid': info.udid}

    async def iphone_device_apps(self) -> List[Dict[str, Any]]:
        apps = await self.device_provider.list_installed_apps()
        return [{'bundle_id': app.bundle_id, 'name': app.name, 'version': app.version, 'is_system_app': app.is_system_app} for app in apps]

    async def iphone_interface_snapshot(self):
        try:
            img_bytes = await self.engine.take_screenshot()
            page_xml = await self.engine.get_filtered_page_source()
            logger.debug("Snapshot captured: image={} bytes, xml={} chars", len(img_bytes), len(page_xml or ""))

            # Compress image to JPEG, target size <= 500k
            img = Image.open(io.BytesIO(img_bytes))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            quality = 85
            while True:
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=quality)
                compressed_size = output.tell()
                if compressed_size <= 500 * 1024 or quality <= 10:
                    break
                quality -= 5
            img_base64 = base64.b64encode(output.getvalue()).decode('utf-8')
            logger.debug("Compressed image to JPEG: {} bytes", compressed_size)

            return [ImageContent(type="image", data=img_base64, mimeType="image/jpeg"), TextContent(type="text", text=page_xml or "<?xml version='1.0'?><page/>")]
        except Exception as e:
            logger.error("Failed to capture interface snapshot: {}", str(e))
            return [TextContent(type="text", text="<?xml version='1.0'?><error>Failed to capture interface</error>")]

    async def iphone_interface_elements(self) -> List[Dict[str, Any]]:
        elems: List[Element] = await self.engine.list_elements()
        return [{'id': elem.id, 'type': elem.type, 'label': elem.label, 'bounds': elem.bounds, 'visible': elem.visible} for elem in elems]

    async def iphone_operate_click(self, x: int, y: int) -> bool:
        return await self.engine.click(x, y)

    async def iphone_operate_swipe(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        return await self.engine.swipe(start_x, start_y, end_x, end_y)

    async def iphone_operate_text_input(self, text: str) -> bool:
        return await self.engine.text_input(text)

    async def iphone_operate_app_launch(self, bundle_id: str) -> bool:
        return await self.engine.launch_app(bundle_id)

    async def iphone_operate_get_current_bundle_id(self) -> str:
        return self.engine.current_bundle_id
