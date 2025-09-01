from __future__ import annotations

from typing import Any, Dict, List

from ..server import MCPServer


def register_tools(mcp_fast, core: MCPServer) -> None:
    @mcp_fast.tool(name="iphone_device_info", description="Get device information")
    async def _t_device_info() -> Dict[str, Any]:
        return await core.iphone_device_info()

    @mcp_fast.tool(name="iphone_device_apps", description="List installed applications")
    async def _t_device_apps() -> List[Dict[str, Any]]:
        return await core.iphone_device_apps()

    @mcp_fast.tool(name="iphone_interface_snapshot", description="Get screenshot (base64 image) + page source (text) multi-part list")
    async def _t_snapshot():
        return await core.iphone_interface_snapshot()

    @mcp_fast.tool(name="iphone_interface_elements", description="List key UI elements")
    async def _t_elements() -> List[Dict[str, Any]]:
        return await core.iphone_interface_elements()

    @mcp_fast.tool(name="iphone_operate_click", description="Tap coordinates")
    async def _t_click(x: int, y: int) -> bool:
        return await core.iphone_operate_click(x, y)

    @mcp_fast.tool(name="iphone_operate_swipe", description="Swipe from start to end coordinates")
    async def _t_swipe(start_x: int, start_y: int, end_x: int, end_y: int) -> bool:
        return await core.iphone_operate_swipe(start_x, start_y, end_x, end_y)

    @mcp_fast.tool(name="iphone_operate_text_input", description="Send text to active element")
    async def _t_text_input(text: str) -> bool:
        return await core.iphone_operate_text_input(text)

    @mcp_fast.tool(name="iphone_operate_app_launch", description="Launch app by bundle id")
    async def _t_app_launch(bundle_id: str) -> bool:
        return await core.iphone_operate_app_launch(bundle_id)

    @mcp_fast.tool(name="iphone_operate_get_current_bundle_id", description="Get current bundle id")
    async def _t_get_current_bundle_id() -> str:
        return await core.iphone_operate_get_current_bundle_id()
