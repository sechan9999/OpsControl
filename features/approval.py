import os
from dataclasses import replace
from typing import Optional

from opscontrol.store import Desk

from .email import DeliveryReceipt, EmailSender, deliver_customer_email
from .feedback_loop import record_feedback

DEFAULT_PIN = "2468"


def get_expected_pin() -> str:
    return os.getenv("FREIGHTDESK_APPROVAL_PIN", os.getenv("OPSCONTROL_APPROVAL_PIN", DEFAULT_PIN))


def verify_pin(pin: str | None) -> bool:
    if not pin:
        return False
    return pin.strip() == get_expected_pin()


def approve_and_send(
    desk: Desk,
    exception_id: int,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    sender: EmailSender | None = None,
    operator_name: str = "Operator",
    pin: Optional[str] = None,
) -> DeliveryReceipt:
    """Apply operator edits, deliver the draft, and mark the record sent."""
    # If PIN is provided in function call, verify it (raises if invalid)
    if pin is not None and not verify_pin(pin):
        raise ValueError("invalid approval PIN")

    record = _get_record(desk, exception_id)

    if record.status not in {"ready_for_approval", "needs_human_review"}:
        raise ValueError(
            f"exception {exception_id} cannot be approved from status '{record.status}'"
        )

    if record.draft is None:
        raise ValueError(f"exception {exception_id} does not have a draft")

    if subject is not None or body is not None:
        new_subject = subject.strip() if subject is not None else record.draft.email_subject
        new_body = body.strip() if body is not None else record.draft.email_body
        desk.save_draft(exception_id, replace(
            record.draft,
            email_subject=new_subject,
            email_body=new_body,
        ))
        # Reload after save so delivery sees the updated draft
        record = _get_record(desk, exception_id)

    if not record.draft.email_subject:
        raise ValueError("email subject cannot be empty")

    if not record.draft.email_body:
        raise ValueError("email body cannot be empty")

    # Delivery occurs before the terminal state transition. If a production
    # adapter fails, the record remains available for operator retry.
    receipt = deliver_customer_email(
        record.draft,
        record.triage.shipment_ref,
        record.status,
        sender,
    )

    desk.set_status(exception_id, "sent")
    desk.log(
        "info",
        "customer_email_sent",
        id=exception_id,
        ref=record.triage.shipment_ref or "-",
        mode=receipt.mode,
        message_id=receipt.message_id,
        by=operator_name.strip() or "Operator",
    )
    record_feedback(desk, exception_id, "approved")

    return receipt


def send_to_review(
    desk: Desk,
    exception_id: int,
    note: str = "operator requested review",
    reason: Optional[str] = None,
    by: str = "operator",
) -> None:
    record = _get_record(desk, exception_id)

    if record.status != "ready_for_approval":
        raise ValueError(
            f"exception {exception_id} cannot move to review from '{record.status}'"
        )

    actual_note = reason if reason is not None else note

    desk.set_status(exception_id, "needs_human_review")
    desk.log("warning", "sent_to_review", id=exception_id, by=by)
    record_feedback(desk, exception_id, "sent_to_review", actual_note)


def dismiss_exception(
    desk: Desk,
    exception_id: int,
    note: str = "",
    reason: Optional[str] = None,
    by: str = "operator",
) -> None:
    record = _get_record(desk, exception_id)

    if record.status in {"sent", "dismissed"}:
        raise ValueError(
            f"exception {exception_id} is already terminal ({record.status})"
        )

    actual_note = reason if reason is not None else note

    desk.set_status(exception_id, "dismissed")
    desk.log("info", "dismissed", id=exception_id, by=by)
    record_feedback(desk, exception_id, "dismissed", actual_note)


def _get_record(desk: Desk, exception_id: int):
    try:
        return desk.exceptions[exception_id]
    except KeyError as exc:
        raise KeyError(f"unknown exception {exception_id}") from exc
