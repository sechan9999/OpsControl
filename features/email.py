from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from opscontrol.models import ExceptionRecord


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
    record: ExceptionRecord,
    sender: EmailSender | None = None,
) -> DeliveryReceipt:
    """Deliver an operator-approved draft through the configured adapter.

    The default adapter records deterministic demo delivery and performs no
    network request.
    """
    if record.status not in {"ready_for_approval", "needs_human_review"}:
        raise ValueError(
            f"exception {record.id} cannot be delivered from status '{record.status}'"
        )

    if record.draft is None:
        raise ValueError(f"exception {record.id} does not have a customer draft")

    delivery = sender or DemoEmailSender()
    reference = record.triage.shipment_ref or f"exception-{record.id}"

    return delivery.send(
        reference=reference,
        subject=record.draft.email_subject,
        body=record.draft.email_body,
    )
