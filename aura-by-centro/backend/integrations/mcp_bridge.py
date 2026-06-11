"""
Aura (by Centro) — Model Context Protocol (MCP) executor.

A lightweight async bridge that fronts the Zoho / Odoo / Genesys MCP servers.
The Central Manager Agent calls `execute()` ONLY after an Action Card has been
confirmed for mutating intents. Read-only tools may be called directly.

The exact runtime contract (endpoints, payload shape) is NOT hard-coded here —
it is fetched at task time from the technical vector space (see FEATURE 4 in
agent.py). This module only knows how to talk MCP.
"""
from __future__ import annotations

from typing import Any

import httpx

from config import get_settings


class MCPError(RuntimeError):
    pass


class MCPBridge:
    """Routes tool calls to the correct MCP server by system name."""

    def __init__(self) -> None:
        s = get_settings()
        self._routes = {
            "zoho": s.zoho_mcp_url,
            "odoo": s.odoo_mcp_url,
            "genesys": s.genesys_mcp_url,
        }
        self._client = httpx.AsyncClient(timeout=60.0)

    def _resolve(self, system: str) -> str:
        base = self._routes.get(system.lower())
        if not base:
            raise MCPError(f"No MCP route registered for system '{system}'")
        return base.rstrip("/")

    async def call_tool(
        self, system: str, tool: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Invoke an MCP tool using the JSON-RPC `tools/call` method.
        Returns the structured tool result or raises MCPError.
        """
        base = self._resolve(system)
        request = {
            "jsonrpc": "2.0",
            "id": f"{system}:{tool}",
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        }
        try:
            resp = await self._client.post(f"{base}/mcp", json=request)
            resp.raise_for_status()
        except httpx.HTTPError as exc:  # network / 5xx / timeout
            raise MCPError(f"MCP call to {system}.{tool} failed: {exc}") from exc

        body = resp.json()
        if "error" in body:
            raise MCPError(f"{system}.{tool} returned error: {body['error']}")
        return body.get("result", {})

    async def list_tools(self, system: str) -> list[dict[str, Any]]:
        base = self._resolve(system)
        resp = await self._client.post(
            f"{base}/mcp",
            json={"jsonrpc": "2.0", "id": "list", "method": "tools/list"},
        )
        resp.raise_for_status()
        return resp.json().get("result", {}).get("tools", [])

    async def aclose(self) -> None:
        await self._client.aclose()


_bridge: MCPBridge | None = None


def get_mcp_bridge() -> MCPBridge:
    global _bridge
    if _bridge is None:
        _bridge = MCPBridge()
    return _bridge
