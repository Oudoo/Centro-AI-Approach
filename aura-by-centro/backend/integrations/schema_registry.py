"""
Aura (by Centro) — FEATURE 4: Dynamic API Schema Retrieval.

Integration contracts (Odoo, Zoho, Genesys, custom ETL) are NOT hard-coded into
LLM prompts. They are registered as flat JSON/Markdown files under
`/documentation/schemas_registry/` and ingested into a dedicated technical
vector space. At task time the Central Manager Agent resolves the *currently
active* runtime contract for an intent via metadata-filtered vector lookup,
falling back to the on-disk registry when the vector store is cold.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

from models import UserContext

log = structlog.get_logger("aura.schema_registry")

# Resolve <repo>/documentation/schemas_registry regardless of CWD.
REGISTRY_DIR = (
    Path(__file__).resolve().parents[2] / "documentation" / "schemas_registry"
)


class SchemaRegistry:
    """Loads + indexes integration contracts and resolves them per intent."""

    def __init__(self) -> None:
        self._by_intent: dict[str, dict[str, Any]] = {}

    async def load(self) -> None:
        """Read every JSON contract from the on-disk registry."""
        self._by_intent.clear()
        if not REGISTRY_DIR.exists():
            log.warning("registry_dir_missing", path=str(REGISTRY_DIR))
            return
        for path in REGISTRY_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except ValueError as exc:
                log.error("schema_parse_failed", file=path.name, error=str(exc))
                continue
            for intent in data.get("intents", []):
                self._by_intent[intent] = data
        log.info("schema_registry_loaded", intents=sorted(self._by_intent))

    async def resolve(self, intent: str, user: UserContext) -> dict[str, Any]:
        """
        Return the active runtime contract for an intent. In production this
        first queries the technical vector space (SCHEMA_COLLECTION) for the
        contract live in WorkDrive; here we resolve from the loaded registry.
        """
        contract = self._by_intent.get(intent)
        if contract is None:
            log.warning("no_contract_for_intent", intent=intent)
            return {
                "target_system": intent,
                "summary": f"Execute '{intent}'.",
                "risk_level": "high",
                "mcp_system": "odoo",
                "mcp_tool": intent,
            }
        return contract


_registry: SchemaRegistry | None = None


async def get_schema_registry() -> SchemaRegistry:
    global _registry
    if _registry is None:
        _registry = SchemaRegistry()
        await _registry.load()
    return _registry
