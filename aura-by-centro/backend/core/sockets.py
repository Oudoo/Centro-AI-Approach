"""
Aura (by Centro) — WebSocket connection registry & message broker.

Wraps the raw Starlette WebSocket so the rest of the system only ever speaks the
typed `SocketMessage` contract. Also tracks pending Action Cards per session so a
write can only fire after a matching, confirmed `action_response`.
"""
from __future__ import annotations

import asyncio

from fastapi import WebSocket

from models import (
    ActionCardData,
    SocketMessage,
    SocketPayload,
    SocketStatus,
)


class Connection:
    """A single live client session."""

    def __init__(self, session_id: str, websocket: WebSocket) -> None:
        self.session_id = session_id
        self.ws = websocket
        self._send_lock = asyncio.Lock()
        # action_id -> future resolved by the client's signed confirmation
        self.pending_actions: dict[str, asyncio.Future[bool]] = {}

    async def send(self, message: SocketMessage) -> None:
        # Serialize sends so interleaved stream tokens never corrupt a frame.
        async with self._send_lock:
            await self.ws.send_text(message.model_dump_json())

    async def stream_token(self, text: str) -> None:
        await self.send(
            SocketMessage(
                status=SocketStatus.STREAMING,
                session_id=self.session_id,
                payload=SocketPayload(text=text),
            )
        )

    async def complete(self, text: str = "") -> None:
        await self.send(
            SocketMessage(
                status=SocketStatus.COMPLETED,
                session_id=self.session_id,
                payload=SocketPayload(text=text),
            )
        )

    async def error(self, text: str) -> None:
        await self.send(
            SocketMessage(
                status=SocketStatus.ERROR,
                session_id=self.session_id,
                payload=SocketPayload(text=text),
            )
        )

    async def request_action(self, card: ActionCardData) -> asyncio.Future[bool]:
        """Emit an Action Card and return a future awaiting the signed reply."""
        future: asyncio.Future[bool] = asyncio.get_running_loop().create_future()
        self.pending_actions[card.action_id] = future
        await self.send(
            SocketMessage(
                status=SocketStatus.ACTION_CARD,
                session_id=self.session_id,
                payload=SocketPayload(card_data=card),
            )
        )
        return future

    def resolve_action(self, action_id: str, confirmed: bool) -> bool:
        future = self.pending_actions.pop(action_id, None)
        if future and not future.done():
            future.set_result(confirmed)
            return True
        return False


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, Connection] = {}
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, websocket: WebSocket) -> Connection:
        await websocket.accept()
        conn = Connection(session_id, websocket)
        async with self._lock:
            self._connections[session_id] = conn
        return conn

    async def disconnect(self, session_id: str) -> None:
        async with self._lock:
            conn = self._connections.pop(session_id, None)
        if conn:
            for fut in conn.pending_actions.values():
                if not fut.done():
                    fut.cancel()

    def get(self, session_id: str) -> Connection | None:
        return self._connections.get(session_id)


manager = ConnectionManager()
