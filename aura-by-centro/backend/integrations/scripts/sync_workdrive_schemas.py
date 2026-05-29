"""
Aura (by Centro) — Existing custom synchronization logic (placeholder).

Pulls the latest integration contracts from Zoho WorkDrive and writes them into
`/documentation/schemas_registry/` so FEATURE 4 always resolves the live
runtime contract. Wire this into a cron / Railway scheduled job.

This is a thin, dependency-light skeleton; replace the `_fetch_*` stubs with the
real WorkDrive + Odoo introspection calls used by your ETL pipeline.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx

from config import get_settings

REGISTRY_DIR = (
    Path(__file__).resolve().parents[3] / "documentation" / "schemas_registry"
)


async def _fetch_workdrive_contracts(client: httpx.AsyncClient) -> list[dict]:
    """TODO: replace with real Zoho WorkDrive folder listing + file download."""
    return []


async def sync() -> None:
    settings = get_settings()
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=60.0) as client:
        contracts = await _fetch_workdrive_contracts(client)
        for contract in contracts:
            name = contract.get("name", "contract").lower().replace(" ", "_")
            (REGISTRY_DIR / f"{name}.json").write_text(
                json.dumps(contract, indent=2), encoding="utf-8"
            )
    print(f"Synced {len(contracts)} contract(s) into {REGISTRY_DIR}")


if __name__ == "__main__":
    asyncio.run(sync())
