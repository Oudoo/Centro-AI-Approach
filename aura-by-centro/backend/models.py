"""
Aura (by Centro) — Pydantic v2 DTOs & the canonical WebSocket message contract.

Every frame that crosses the socket MUST conform to `SocketMessage`. This keeps
the Next.js client and the FastAPI server in lock-step (see CODE PATTERN #3).
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Identity / RBAC context resolved from the auth token on connect
# -----------------------------------------------------------------------------
class UserContext(BaseModel):
    user_id: str
    display_name: str = "Centro User"
    department: str = "general"
    account_scope: str = "global"          # coastline | trueblue | global
    role: str = "agent"                    # agent | team_lead | manager | admin


# -----------------------------------------------------------------------------
# Socket envelope
# -----------------------------------------------------------------------------
class SocketStatus(str, Enum):
    STREAMING = "streaming"
    COMPLETED = "completed"
    ACTION_CARD = "action_card"
    ERROR = "error"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FormField(BaseModel):
    name: str
    type: str
    label: str
    required: bool = True


class ActionCardData(BaseModel):
    """Payload rendered by the frontend `action-card.tsx` for dual confirmation."""

    action_id: str
    intent: str
    target_system: str                      # e.g. "Odoo Payroll", "Trueblue Scheduling"
    summary: str
    api_payload: dict[str, Any] = Field(default_factory=dict)
    form_fields: Optional[list[FormField]] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_assessment: str = ""


class SocketPayload(BaseModel):
    text: str = ""
    card_data: Optional[ActionCardData] = None


class SocketMessage(BaseModel):
    """The ONLY shape that may be sent over the WebSocket."""

    status: SocketStatus
    session_id: str
    payload: SocketPayload = Field(default_factory=SocketPayload)


# -----------------------------------------------------------------------------
# Inbound client frames
# -----------------------------------------------------------------------------
class ClientMessageType(str, Enum):
    QUERY = "query"
    ACTION_RESPONSE = "action_response"


class ClientQuery(BaseModel):
    type: Literal[ClientMessageType.QUERY] = ClientMessageType.QUERY
    session_id: str
    text: str


class ClientActionResponse(BaseModel):
    """Signed reply to an Action Card. Write only fires when confirmed is True."""

    type: Literal[ClientMessageType.ACTION_RESPONSE] = ClientMessageType.ACTION_RESPONSE
    session_id: str
    action_id: str
    action_confirmed: bool = False
    form_data: dict[str, Any] = Field(default_factory=dict)
    signature: Optional[str] = None         # HMAC over (session_id|action_id)


# -----------------------------------------------------------------------------
# Internal pipeline DTOs
# -----------------------------------------------------------------------------
class RetrievedChunk(BaseModel):
    text: str                 # the (child) text that matched / was embedded
    score: float
    department: str
    account_scope: str
    min_role_required: str
    source: str = ""
    parent_text: str = ""     # the larger parent section to send to the LLM
    doc_id: str = ""

    @property
    def context(self) -> str:
        """Text to hand to the LLM: prefer the parent section if present."""
        return self.parent_text or self.text
