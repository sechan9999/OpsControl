import os
import smtplib
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Optional, Protocol

from opscontrol.models import Draft


@dataclass(frozen=True)
class DeliveryReceipt:
    message_id: str
    mode: str
    accepted_at: str


class EmailSender(Protocol):
    def send(
        self,
        *,
        reference: str,
        subject: str,
        body: str,
    ) -> DeliveryReceipt:
        ...


class DemoEmailSender:
    """Credential-free sender used by the public deterministic demo."""

    def send(
        self,
        *,
        reference: str,
        subject: str,
        body: str,
    ) -> DeliveryReceipt:
        del subject, body

        return DeliveryReceipt(
            message_id=f"demo-{reference}",
            mode="mock",
            accepted_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )


class SMTPEmailSender:
    """Real SMTP email sender when FREIGHTDESK_SMTP_HOST / OPSCONTROL_SMTP_HOST is configured."""

    def __init__(self, host: str, port: int = 587, username: str = "", password: str = "", sender_email: str = ""):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.sender_email = sender_email or username or "opscontrol@example.com"

    def send(
        self,
        *,
        reference: str,
        subject: str,
        body: str,
    ) -> DeliveryReceipt:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg.set_content(body)

        with smtplib.SMTP(self.host, self.port) as smtp:
            if self.username and self.password:
                smtp.starttls()
                smtp.login(self.username, self.password)
            # Send message
            smtp.send_message(msg)

        return DeliveryReceipt(
            message_id=f"smtp-{reference}",
            mode="smtp",
            accepted_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )


def get_default_sender() -> EmailSender:
    host = os.getenv("FREIGHTDESK_SMTP_HOST", os.getenv("OPSCONTROL_SMTP_HOST", "")).strip()
    if host:
        port = int(os.getenv("FREIGHTDESK_SMTP_PORT", os.getenv("OPSCONTROL_SMTP_PORT", "587")))
        user = os.getenv("FREIGHTDESK_SMTP_USER", os.getenv("OPSCONTROL_SMTP_USER", ""))
        pwd = os.getenv("FREIGHTDESK_SMTP_PASS", os.getenv("OPSCONTROL_SMTP_PASS", ""))
        from_email = os.getenv("FREIGHTDESK_SMTP_FROM", os.getenv("OPSCONTROL_SMTP_FROM", ""))
        return SMTPEmailSender(host=host, port=port, username=user, password=pwd, sender_email=from_email)
    return DemoEmailSender()


def deliver_customer_email(
    draft: Draft,
    shipment_ref: Optional[str],
    status: str,
    sender: EmailSender | None = None,
) -> DeliveryReceipt:
    """Deliver an operator-approved draft through the configured adapter."""
    if status not in {"ready_for_approval", "needs_human_review"}:
        raise ValueError(
            f"cannot deliver from status '{status}'"
        )

    delivery = sender or get_default_sender()
    reference = shipment_ref or f"exception-unknown"

    return delivery.send(
        reference=reference,
        subject=draft.email_subject,
        body=draft.email_body,
    )
