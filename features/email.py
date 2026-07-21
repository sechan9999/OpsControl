from dataclasses import dataclass
from datetime import datetime, timezone
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
            mode="demo",
            accepted_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )


def deliver_customer_email(
    draft: Draft,
    shipment_ref: Optional[str],
    status: str,
    sender: EmailSender | None = None,
) -> DeliveryReceipt:
    """Deliver an operator-approved draft through the configured adapter.

    Accepts the three record fields it actually needs instead of the full
    ``ExceptionRecord``, reducing coupling to the data model.

    The default adapter records deterministic demo delivery and performs no
    network request.
    """
    if status not in {"ready_for_approval", "needs_human_review"}:
        raise ValueError(
            f"cannot deliver from status '{status}'"
        )

    delivery = sender or DemoEmailSender()
    reference = shipment_ref or f"exception-unknown"

    return delivery.send(
        reference=reference,
        subject=draft.email_subject,
        body=draft.email_body,
    )
