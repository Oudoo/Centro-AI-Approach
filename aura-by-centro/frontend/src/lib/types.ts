/** Mirror of the backend WebSocket contract (backend/models.py). */

export type SocketStatus = "streaming" | "completed" | "action_card" | "error";

export type RiskLevel = "low" | "medium" | "high";

export interface ActionCardData {
  action_id: string;
  intent: string;
  target_system: string;
  summary: string;
  api_payload: Record<string, unknown>;
  risk_level: RiskLevel;
  risk_assessment: string;
}

export interface SocketPayload {
  text?: string;
  card_data?: ActionCardData | null;
}

export interface SocketMessage {
  status: SocketStatus;
  session_id: string;
  payload: SocketPayload;
}

export type ChatRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  streaming?: boolean;
  card?: ActionCardData;
  cardResolved?: "confirmed" | "cancelled";
}
