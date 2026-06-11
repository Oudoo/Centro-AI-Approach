"""
Aura (by Centro) — Zoho People integration (MCP-backed).

When `ZOHO_INTEGRATION_ENABLED=true` and a Zoho People MCP server is reachable
at `ZOHO_MCP_URL`, a confirmed employee request (leave / shift swap / break) is
posted to Zoho via the MCP bridge using the tool named in the request's schema
contract (`mcp_system` + `mcp_tool`). Otherwise we stay in demo mode and the
request is only stored + emailed.

This keeps the live integration a config flip — no code change — and never
breaks the chat: any failure degrades gracefully to the demo path.
"""
from __future__ import annotations

import structlog

from config import get_settings
from integrations.mcp_bridge import MCPError, get_mcp_bridge
from models import UserContext

log = structlog.get_logger("aura.zoho")


async def submit_to_zoho(contract: dict, user: UserContext, details: dict) -> tuple[bool, str]:
    """
    Returns (submitted, note). `submitted` is False in demo mode or on failure;
    the caller still records + emails the request as the audit trail.
    """
    s = get_settings()
    if not s.zoho_integration_enabled:
        return False, "Zoho integration disabled (demo mode)."

    bridge = get_mcp_bridge()
    system = contract.get("mcp_system", "zoho")
    tool = contract.get("mcp_tool", "")
    # Map the employee context + form fields into the tool arguments. The exact
    # shape is owned by the schema contract + the Zoho MCP server.
    arguments = {
        "employee_id": details.get("employee_id") or user.user_id,
        "employee_name": user.display_name,
        "account_scope": user.account_scope,
        "department": user.department,
        **contract.get("example_payload", {}),
        **details,
    }
    try:
        result = await bridge.call_tool(system, tool, arguments)
        log.info("zoho_submitted", tool=tool, employee=user.user_id)
        ref = ""
        if isinstance(result, dict):
            ref = str(result.get("id") or result.get("recordId") or "")
        return True, f"Filed in Zoho People{f' (ref {ref})' if ref else ''}."
    except MCPError as exc:
        log.error("zoho_submit_failed", tool=tool, error=str(exc))
        return False, f"Zoho submission failed: {exc}"
