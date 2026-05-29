"""
Aura (by Centro) — Email notifier for employee requests.

During the demo phase, submitted requests email a single inbox
(REQUEST_NOTIFY_EMAIL, default mahmoud.hassan@centrocdx.com). When SMTP is not
configured we run in "demo mode": the email is composed and logged but not sent,
so the flow still works end-to-end without credentials. Wire real SMTP (or swap
for the Zoho People MCP) by setting the SMTP_* env vars.
"""
from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

import structlog

from config import get_settings

log = structlog.get_logger("aura.notifier")


def _format_body(request_type: str, target_system: str, user, details: dict) -> str:
    lines = [
        f"New {request_type.replace('_', ' ').title()} request via Aura (by Centro)",
        "",
        f"Employee:       {getattr(user, 'display_name', '')} ({getattr(user, 'user_id', '')})",
        f"Account scope:  {getattr(user, 'account_scope', '')}",
        f"Department:     {getattr(user, 'department', '')}",
        f"Target system:  {target_system}",
        "",
        "Request details:",
    ]
    for k, v in details.items():
        lines.append(f"  - {k.replace('_', ' ').title()}: {v}")
    lines += ["", "— Sent automatically by Aura. Demo phase routing."]
    return "\n".join(lines)


def _send_sync(subject: str, body: str, to_addr: str) -> bool:
    s = get_settings()
    if not s.smtp_host:
        return False  # demo mode — no SMTP configured
    msg = EmailMessage()
    msg["From"] = s.smtp_from
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=20) as server:
        if s.smtp_use_tls:
            server.starttls()
        if s.smtp_user:
            server.login(s.smtp_user, s.smtp_password)
        server.send_message(msg)
    return True


async def notify_request(request_type: str, target_system: str, user, details: dict) -> tuple[bool, str]:
    """
    Returns (sent, to_address). `sent` is False in demo mode (no SMTP) — the
    request is still recorded; we just didn't transmit an email.
    """
    s = get_settings()
    to_addr = s.request_notify_email
    subject = f"[Aura] {request_type.replace('_', ' ').title()} — {getattr(user, 'display_name', 'Employee')}"
    body = _format_body(request_type, target_system, user, details)
    try:
        sent = await asyncio.to_thread(_send_sync, subject, body, to_addr)
        if sent:
            log.info("request_email_sent", to=to_addr, type=request_type)
        else:
            log.info("request_email_demo_mode", to=to_addr, type=request_type)
        return sent, to_addr
    except Exception as exc:  # never let email failure break the request
        log.error("request_email_failed", error=str(exc), to=to_addr)
        return False, to_addr
