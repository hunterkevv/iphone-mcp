from __future__ import annotations

import asyncio
import socket
from typing import Any, Dict, Optional
from loguru import logger

from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.ios import XCUITestOptions
from selenium.webdriver.common.options import ArgOptions


class AppiumDriverManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._driver = None

    def _create_real_driver(self):
        if webdriver is None:
            raise RuntimeError("Appium WebDriver is not available. Please install appium-python-client.")

        appium_cfg = self.config.get("appium", {})
        device_cfg = self.config.get("device", {})
        host = appium_cfg.get("host", "127.0.0.1")
        port = appium_cfg.get("port", 4723)
        udid = device_cfg.get("udid")
        if not udid:
            raise ValueError("UDID is required")

        def is_port_open(h, p):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((h, p))
                return result == 0

        if not is_port_open(host, port):
            raise RuntimeError(f"Appium server not running on {host}:{port}. Please start Appium manually or use start.sh.")

        logger.info("Creating Appium session to {}:{} (udid={})", host, port, udid)

        if XCUITestOptions is not None:
            opts = XCUITestOptions()
            opts.set_capability("udid", udid)
            wda_port = appium_cfg.get("wdaLocalPort", 8100)
            opts.set_capability("wdaLocalPort", wda_port)
            opts.set_capability("newCommandTimeout", appium_cfg.get("newCommandTimeout", 360))
            opts.set_capability("defaultLaunchTimeout", appium_cfg.get("defaultLaunchTimeout", 30000))
            return webdriver.Remote(f"http://{host}:{port}", options=opts)

        caps = {"platformName": appium_cfg.get("platformName", "iOS"), "automationName": appium_cfg.get("automationName", "XCUITest"), "wdaLocalPort": appium_cfg.get("wdaLocalPort", 8100), "udid": udid, "newCommandTimeout": appium_cfg.get("newCommandTimeout", 360), "defaultLaunchTimeout": appium_cfg.get("defaultLaunchTimeout", 30000)}
        try:
            return webdriver.Remote(f"http://{host}:{port}", options=ArgOptions(), desired_capabilities=caps)
        except Exception:
            return webdriver.Remote(f"http://{host}:{port}", caps)

    async def get_driver(self):
        if self._driver:
            return self._driver
        self._driver = await asyncio.to_thread(self._create_real_driver)
        return self._driver

    async def quit_driver(self) -> None:
        if self._driver:
            drv = self._driver
            self._driver = None
            await asyncio.to_thread(drv.quit)
