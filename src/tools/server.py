from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..server import MCPServer
from .registry import register_tools
from mcp.server.fastmcp import FastMCP


def build_streamable_http_server(config: Optional[Dict[str, Any]] = None) -> FastMCP:
    core = MCPServer(config=config)

    cfg = core.config
    server_cfg = cfg.get("server", {}) if isinstance(cfg, dict) else {}
    host = server_cfg.get("host", "127.0.0.1")
    port = int(server_cfg.get("port", 8765))
    http_path = server_cfg.get("path", "/mcp") or "/mcp"

    mcp_fast = FastMCP(
        name="iphone-mcp",
        instructions="iPhone automation bridge",
        host=host,
        port=port,
        streamable_http_path=http_path,
    )

    register_tools(mcp_fast, core)

    print(f"MCP streamable-http server starting at http://{host}:{port}{http_path} (tools registered: {len(core._methods)})")
    return mcp_fast
