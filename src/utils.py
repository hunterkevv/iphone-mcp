from __future__ import annotations

import os
from typing import Any, Dict
from loguru import logger

_runtime_config: Dict[str, Any] | None = None

_DEFAULT_CONFIG: Dict[str, Any] = {
    "appium": {
        "host": os.getenv("APPIUM_HOST"),
        "port": int(os.getenv("APPIUM_PORT")),
        "platformName": os.getenv("PLATFORM_NAME"),
        "automationName": os.getenv("AUTOMATION_NAME"),
        "wdaLocalPort": int(os.getenv("WDA_LOCAL_PORT")),
        "defaultLaunchTimeout": int(os.getenv("DEFAULT_LAUNCH_TIMEOUT")),
        "newCommandTimeout": int(os.getenv("NEW_COMMAND_TIMEOUT")),
    },
    "device": {
        "udid": os.getenv("DEVICE_UDID"),
        "defaultBundleId": os.getenv("DEFAULT_BUNDLE_ID"),
    },
    "logging": {
        "level": os.getenv("LOG_LEVEL"),
    },
    "server": {
        "host": os.getenv("SERVER_HOST"),
        "port": int(os.getenv("SERVER_PORT")),
        "path": os.getenv("SERVER_PATH"),
    },
}


def set_runtime_config(cfg: Dict[str, Any]) -> None:
    global _runtime_config
    _runtime_config = cfg
    logger.debug("Runtime config set: {}", cfg)


def load_config(refresh: bool = False) -> Dict[str, Any]:
    if _runtime_config is not None and not refresh:
        return _runtime_config
    logger.debug("Using default in-memory config")
    return {k: (v.copy() if isinstance(v, dict) else v) for k, v in _DEFAULT_CONFIG.items()}


def get_config_section(section: str) -> Dict[str, Any]:
    cfg = load_config()
    if section not in cfg:
        raise KeyError(f"Missing config section: {section}")
    return cfg[section]


class FrameworkError(Exception):
    pass


class DeviceNotFoundError(FrameworkError):
    pass


class AppLaunchError(FrameworkError):
    pass


class ElementNotFoundError(FrameworkError):
    pass
