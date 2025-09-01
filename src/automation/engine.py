from __future__ import annotations

import asyncio
import base64
from typing import Any, Dict, List
from loguru import logger

from ..utils import AppLaunchError, ElementNotFoundError
from .models import Element
from .driver import AppiumDriverManager, AppiumBy
from .interface_element_processor import InterfaceElementProcessor


class XCUITestEngine:
    """Engine for XCUITest automation using Appium."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.driver_manager = AppiumDriverManager(config)
        self.interface_processor = InterfaceElementProcessor()
        self._lock = asyncio.Lock()
        self.current_bundle_id = config.get("device", {}).get("defaultBundleId", "")

    async def _ensure_driver(self):
        """Ensure driver is available."""
        return await self.driver_manager.get_driver()

    async def quit(self) -> None:
        """Quit the driver."""
        await self.driver_manager.quit_driver()

    async def launch_app(self, bundle_id: str) -> bool:
        """Launch an application by bundle ID."""
        driver = await self._ensure_driver()
        try:
            logger.info("Launching app {}", bundle_id)
            await asyncio.to_thread(
                driver.execute_script, "mobile: launchApp", {"bundleId": bundle_id}
            )
            self.current_bundle_id = bundle_id
            return True
        except Exception as e:
            raise AppLaunchError(str(e)) from e

    async def switch_app(self, bundle_id: str) -> bool:
        """Switch to an existing application by bundle ID."""
        driver = await self._ensure_driver()
        try:
            logger.info("Activating app {}", bundle_id)
            await asyncio.to_thread(
                driver.execute_script, "mobile: activateApp", {"bundleId": bundle_id}
            )
            self.current_bundle_id = bundle_id
            return True
        except Exception as e:
            raise AppLaunchError(str(e)) from e

    async def take_screenshot(self) -> bytes:
        """Take a screenshot."""
        driver = await self._ensure_driver()
        b64 = await asyncio.to_thread(driver.get_screenshot_as_base64)

        return base64.b64decode(b64)

    def is_stub(self) -> bool:
        """Check if using stub driver."""
        return self.driver_manager.is_stub()

    @staticmethod
    def png_dimensions(png_bytes: bytes) -> tuple[int | None, int | None]:
        """Get PNG dimensions."""
        if len(png_bytes) < 24:
            return (None, None)
        if not png_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return (None, None)
        import struct

        try:
            width = struct.unpack(">I", png_bytes[16:20])[0]
            height = struct.unpack(">I", png_bytes[20:24])[0]
            return (int(width), int(height))
        except Exception:
            return (None, None)

    async def get_page_source(self) -> str:
        """Get raw page source."""
        driver = await self._ensure_driver()
        return await asyncio.to_thread(lambda: driver.page_source)

    async def get_filtered_page_source(self) -> str:
        """Get filtered page source."""
        raw = await self.get_page_source()
        return self.interface_processor.filter_page_source(raw)

    async def list_elements(self) -> List[Element]:
        """List UI elements."""
        driver = await self._ensure_driver()
        found: List[Element] = []
        target_classes = [
            "XCUIElementTypeButton",
            "XCUIElementTypeStaticText",
            "XCUIElementTypeTextField",
            "XCUIElementTypeImage",
        ]

        def blocking():
            elems = []
            for cls in target_classes:
                try:
                    elems.extend(driver.find_elements(AppiumBy.CLASS_NAME, cls))
                except Exception:
                    continue
            return elems

        raw = await asyncio.to_thread(blocking)
        for e in raw:
            try:
                rect = e.rect
                bounds = {
                    "x": int(rect.get("x", 0)),
                    "y": int(rect.get("y", 0)),
                    "width": int(rect.get("width", 0)),
                    "height": int(rect.get("height", 0)),
                }
                found.append(
                    Element(
                        id=str(e.id),
                        type=str(e.get_attribute("type") or ""),
                        label=e.get_attribute("label") or e.text or "",
                        bounds=bounds,
                        visible=bool(e.is_displayed()),
                    )
                )
            except Exception:
                continue
        return found

    async def click(self, x: int, y: int) -> bool:
        """Perform click at coordinates."""
        driver = await self._ensure_driver()
        await asyncio.to_thread(driver.execute_script, "mobile: tap", {"x": x, "y": y})
        return True

    async def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        """Perform swipe gesture."""
        driver = await self._ensure_driver()
        await asyncio.to_thread(
            driver.execute_script,
            "mobile: dragFromToForDuration",
            {
                "duration": 0.2,
                "fromX": start_x,
                "fromY": start_y,
                "toX": end_x,
                "toY": end_y,
            },
        )
        return True

    async def text_input(self, text: str) -> bool:
        """Input text to active element."""
        driver = await self._ensure_driver()

        def blocking():
            try:
                el = driver.switch_to.active_element
                el.send_keys(text)
                return True
            except Exception as e:
                logger.error("Text input failed: {}", e)
                return False

        return await asyncio.to_thread(blocking)
