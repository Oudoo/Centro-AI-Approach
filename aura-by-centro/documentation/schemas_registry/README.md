# Schemas Registry — Live API Contracts (Aura by Centro)

This folder is the source of truth for **Dynamic API Schema Retrieval (Feature 4)**.

Integration contracts (Odoo, Zoho, Genesys, custom ETL) are stored here as flat
JSON/Markdown files instead of being hard-coded into LLM system prompts. The
`sync_workdrive_schemas.py` script keeps these in sync with the live contracts
published in Zoho WorkDrive.

At runtime the Central Manager Agent ingests these files into the technical
vector space (`SCHEMA_COLLECTION`) and resolves the *currently active* contract
for an intent on demand. Each file declares:

| Field            | Purpose                                                        |
|------------------|----------------------------------------------------------------|
| `intents`        | Mutation intents this contract satisfies                       |
| `target_system`  | Human-readable system name shown on the Action Card            |
| `mcp_system`     | MCP route key (`zoho` \| `odoo` \| `genesys`)                  |
| `mcp_tool`       | MCP tool name invoked on confirmation                          |
| `risk_level`     | `low` \| `medium` \| `high` — drives Action Card styling       |
| `example_payload`| Sample payload rendered on the Action Card for review          |
| `min_role_required` | RBAC gate enforced before the intent is offered             |

> Add a new integration by dropping a `<system>.json` file here — no code change
> required.
