"""
Aura (by Centro) — Global configuration, RBAC scopes & constants.

All runtime configuration is loaded from the environment (see `.env.example`)
via Pydantic v2 `BaseSettings`. Nothing here should be hard-coded per-tenant;
account isolation is driven by the RBAC scope model below.
"""
from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# -----------------------------------------------------------------------------
# RBAC scope model
# -----------------------------------------------------------------------------
class AccountScope(str, Enum):
    """Tenant / account isolation boundaries enforced at the vector index layer."""

    GLOBAL = "global"
    COASTLINE = "coastline"
    TRUEBLUE = "trueblue"


class Role(str, Enum):
    """Hierarchical roles. Higher ordinal => more privilege."""

    AGENT = "agent"
    TEAM_LEAD = "team_lead"
    MANAGER = "manager"
    ADMIN = "admin"


# Numeric rank used for `min_role_required` metadata comparisons.
ROLE_RANK: dict[str, int] = {
    Role.AGENT.value: 10,
    Role.TEAM_LEAD.value: 20,
    Role.MANAGER.value: 30,
    Role.ADMIN.value: 40,
}


def scopes_visible_to(account_scope: str) -> list[str]:
    """
    Return the set of `account_scope` values a user is allowed to retrieve.

    Every tenant can always see GLOBAL knowledge in addition to their own
    account. GLOBAL/ADMIN users implicitly see everything.
    """
    account_scope = (account_scope or "").lower()
    if account_scope == AccountScope.GLOBAL.value:
        return [s.value for s in AccountScope]
    return list({AccountScope.GLOBAL.value, account_scope})


# Intents that mutate external systems and therefore REQUIRE a dual-confirmation
# Action Card before execution (see FEATURE 3).
MUTATION_INTENTS: frozenset[str] = frozenset(
    {
        "swap_shift",
        "annual_leave_request",
        "casual_leave_request",
        "update_break_timing",
    }
)


# -----------------------------------------------------------------------------
# Settings
# -----------------------------------------------------------------------------
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # App
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    allowed_origins: str = Field(default="http://localhost:3000", alias="ALLOWED_ORIGINS")

    # LLM
    llm_base_url: str = Field(default="http://localhost:1234/v1", alias="LLM_BASE_URL")
    llm_api_key: str = Field(default="local-no-key-required", alias="LLM_API_KEY")
    llm_model: str = Field(default="qwen2.5:1.5b", alias="LLM_MODEL")
    llm_context_window: int = Field(default=262144, alias="LLM_CONTEXT_WINDOW")
    llm_max_output_tokens: int = Field(default=768, alias="LLM_MAX_OUTPUT_TOKENS")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")
    llm_request_timeout: int = Field(default=120, alias="LLM_REQUEST_TIMEOUT")

    # Embeddings
    embedding_base_url: str = Field(default="http://localhost:1234/v1", alias="EMBEDDING_BASE_URL")
    embedding_model: str = Field(default="nomic-embed-text", alias="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=768, alias="EMBEDDING_DIM")

    # Vector engine
    vector_backend: str = Field(default="qdrant", alias="VECTOR_BACKEND")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    vector_collection: str = Field(default="aura_knowledge", alias="VECTOR_COLLECTION")
    schema_collection: str = Field(default="aura_schemas", alias="SCHEMA_COLLECTION")

    # CAG
    cag_similarity_threshold: float = Field(default=0.92, alias="CAG_SIMILARITY_THRESHOLD")
    cag_max_entries: int = Field(default=2048, alias="CAG_MAX_ENTRIES")

    # Auth
    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    session_ttl_seconds: int = Field(default=3600, alias="SESSION_TTL_SECONDS")

    # MCP integrations
    zoho_mcp_url: str = Field(default="http://localhost:9001", alias="ZOHO_MCP_URL")
    odoo_mcp_url: str = Field(default="http://localhost:9002", alias="ODOO_MCP_URL")
    genesys_mcp_url: str = Field(default="http://localhost:9003", alias="GENESYS_MCP_URL")

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton accessor so the env is parsed exactly once."""
    return Settings()


# -----------------------------------------------------------------------------
# Brand constants — Centro Brand Book (Pomelli)
# -----------------------------------------------------------------------------
class Brand:
    NAME = "Aura"
    FULL_NAME = "Aura by Centro"
    TAGLINE = "Your AI co-pilot, helping businesses drive meaningful change for growth."
    PRUSSIAN_BLUE = "#004A59"
    PURE_WHITE = "#FFFFFF"
    ONYX_BLACK = "#32373C"
    PRIMARY_FONT = "Roboto"
