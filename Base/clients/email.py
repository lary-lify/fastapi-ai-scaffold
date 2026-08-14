"""Pluggable email sending clients.

The scaffold ships two backends:

* ``ConsoleEmailClient`` (default) — prints the message to stdout. Zero config,
  ideal for local dev, CI and tests.
* ``SmtpEmailClient`` — sends via a real SMTP server (stdlib ``smtplib``,
  wrapped in a thread so it stays async-safe). Configure via ``.env``:

  EMAIL_BACKEND=smtp
  SMTP_HOST=smtp.example.com
  SMTP_PORT=587
  SMTP_USER=apikey
  SMTP_PASSWORD=secret
  EMAIL_FROM=no-reply@example.com

Select the backend with ``EMAIL_BACKEND`` (``console`` | ``smtp``).
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

from Base.config.setting import settings

logger = logging.getLogger(__name__)


class EmailClient(Protocol):
    """Async contract every email backend implements."""

    async def send(self, *, to: str, subject: str, body: str) -> None:  # pragma: no cover
        ...


class ConsoleEmailClient:
    """Default backend: log the email instead of sending it."""

    async def send(self, *, to: str, subject: str, body: str) -> None:
        logger.info("[email:console] to=%s subject=%s\n%s", to, subject, body)


class SmtpEmailClient:
    """SMTP backend using the stdlib synchronously inside a worker thread."""

    def __init__(self) -> None:
        e = settings.email
        self.host = e.smtp_host
        self.port = e.smtp_port
        self.user = e.smtp_user
        self.password = e.smtp_password
        self.from_addr = e.from_addr

    def _send_sync(self, *, to: str, subject: str, body: str) -> None:
        msg = EmailMessage()
        msg["From"] = self.from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(self.host, self.port) as server:
            if self.user:
                server.starttls()
                server.login(self.user, self.password or "")
            server.send_message(msg)

    async def send(self, *, to: str, subject: str, body: str) -> None:
        await asyncio.to_thread(self._send_sync, to=to, subject=subject, body=body)


def get_email_client() -> EmailClient:
    """Factory: pick the backend from ``settings.email.backend``."""
    backend = (settings.email.backend or "console").lower()
    if backend == "smtp":
        return SmtpEmailClient()
    return ConsoleEmailClient()
