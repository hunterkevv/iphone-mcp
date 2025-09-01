#!/usr/bin/env python3

from __future__ import annotations

import sys
import warnings
from typing import Dict, Any
from loguru import logger

warnings.filterwarnings("ignore", message="websockets.legacy is deprecated")
warnings.filterwarnings("ignore", message="websockets.server.WebSocketServerProtocol is deprecated")

from src.tools.server import build_streamable_http_server
from src.utils import load_config, set_runtime_config


def _merge_config(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    merged = {**base}
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = _merge_config(merged[k], v)
        else:
            merged[k] = v
    return merged


def main(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Start iPhone MCP streamable-http server")
    parser.add_argument("--udid", dest="udid", required=True, help="Device UDID (required)")
    parser.add_argument("--host", dest="host", default=None, help="Bind host (default from config or 127.0.0.1)")
    parser.add_argument("--port", dest="port", type=int, default=None, help="Bind port (default 8765)")
    parser.add_argument("--http-path", dest="http_path", default=None, help="Streamable HTTP path (default /mcp)")
    args = parser.parse_args(argv)

    base_cfg = load_config()
    overrides: Dict[str, Any] = {}
    if args.udid:
        overrides.setdefault("device", {})["udid"] = args.udid
    if args.host:
        overrides.setdefault("server", {})["host"] = args.host
    if args.port:
        overrides.setdefault("server", {})["port"] = args.port
    if args.http_path:
        overrides.setdefault("server", {})["path"] = args.http_path

    final_cfg = _merge_config(base_cfg, overrides) if overrides else base_cfg

    if not final_cfg.get("device", {}).get("udid"):
        logger.error("UDID is required but not provided")
        return 1

    set_runtime_config(final_cfg)

    server = build_streamable_http_server(config=final_cfg)
    server_cfg = final_cfg.get("server", {})
    host = server_cfg.get("host", "127.0.0.1")
    port = server_cfg.get("port", 8765)
    path = server_cfg.get("path", "/mcp").rstrip('/') or "/mcp"
    url = f"http://{host}:{port}{path}"
    logger.info("Starting MCP server at {}", url)
    print(url)

    server.run(transport="streamable-http")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
