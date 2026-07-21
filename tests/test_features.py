import pytest

from features.approval import approve_and_send, dismiss_exception, send_to_review
from features.customer_profile import (
    CustomerProfile,
    apply_customer_profile,
    resolve_customer_profile,
)
from features.email import DemoEmailSender, deliver_customer_email
from features.feedback_loop import record_feedback
from features.ingest import ingest_batch, ingest_message, normalize_channel
from opscontrol.config import Settings
from opscontrol.models import Draft
from opscontrol.store import Desk

SETTINGS = Settings()

PHARMA_MESSAGE = (
    "Escalation: OPS-40045-A is temperature-sensitive pharma with a hard delivery "
    "window Thursday 08:00-12:00. Current Savannah hold puts arrival at Thursday "
    "15:40. Client contract has a $25k OTIF penalty clause. Need options today."
)


def make_approval_record(desk: Desk):
    record = ingest_message(PHARMA_MESSAGE, "email", desk, SETTINGS)
    assert record is not None
    assert record.status == "ready_for_approval"
    return record


# ---- ingestion -----------------------------------------------------------

def test_normalize_channel():
    assert normalize_channel(" EDI ") == "edi"
    assert normalize_channel("Email") == "email"

    with pytest.raises(ValueError):
        normalize_channel("fax")


def test_ingest_rejects_empty_message():
    with pytest.raises(ValueError):
        ingest_message("   ", "email", Desk(), SETTINGS)


def test_ingest_batch_preserves_duplicate_suppression():
    desk = Desk()
    messages = [
        {"raw": PHARMA_MESSAGE, "channel": "email"},
        {"raw": PHARMA_MESSAGE, "channel": "email"},
    ]

    results = ingest_batch(messages, desk, SETTINGS)

    assert results[0] is not None
    assert results[1] is None
    assert desk.metrics()["ingested"] == 1
    assert desk.metrics()["duplicates"] == 1


def test_ingest_records_safe_source_metadata():
    desk = Desk()

    record = ingest_message(
        PHARMA_MESSAGE,
        "email",
        desk,
        SETTINGS,
        metadata={"source": "carrier-inbox"},
    )

    assert record is not None
    assert any("source_metadata_attached" in line for line in desk.logs)


# ---- email and approval --------------------------------------------------

def test_demo_email_sender_returns_receipt():
    desk = Desk()
    record = make_approval_record(desk)

    receipt = deliver_customer_email(
        record.draft,
        record.triage.shipment_ref,
        record.status,
        DemoEmailSender(),
    )

    assert receipt.mode == "demo"
    assert receipt.message_id == "demo-OPS-40045-A"
    assert record.status == "ready_for_approval"


def test_approve_and_send_applies_operator_edits():
    desk = Desk()
    record = make_approval_record(desk)

    receipt = approve_and_send(
        desk,
        record.id,
        subject="Updated customer subject",
        body="Updated customer body",
    )

    # Re-fetch the record from the desk — Draft is frozen so approve_and_send
    # saves a new Draft instance via desk.save_draft().
    updated = desk.exceptions[record.id]
    assert receipt.mode == "demo"
    assert updated.status == "sent"
    assert updated.draft.email_subject == "Updated customer subject"
    assert updated.draft.email_body == "Updated customer body"
    assert desk.metrics()["sent"] == 1
    assert any("operator_feedback" in line for line in desk.logs)


def test_approval_rejects_empty_subject():
    desk = Desk()
    record = make_approval_record(desk)

    with pytest.raises(ValueError):
        approve_and_send(desk, record.id, subject="")

    assert record.status == "ready_for_approval"


def test_send_to_review_records_feedback():
    desk = Desk()
    record = make_approval_record(desk)

    send_to_review(desk, record.id, note="Verify customer instructions")

    assert record.status == "needs_human_review"
    assert any("outcome=sent_to_review" in line for line in desk.logs)


def test_dismiss_exception_is_terminal():
    desk = Desk()
    record = make_approval_record(desk)

    dismiss_exception(desk, record.id, note="Duplicate business event")

    assert record.status == "dismissed"

    with pytest.raises(ValueError):
        dismiss_exception(desk, record.id)


# ---- customer profiles --------------------------------------------------

def test_customer_profile_adjusts_greeting_and_signoff():
    draft = Draft(
        email_subject="Shipment update",
        email_body="Hello,\n\nYour shipment is delayed.\n\nOpsControl Operations",
        action_plan="Contact carrier",
    )
    profile = CustomerProfile(
        customer_id="customer-1",
        greeting="Hello Acme team,",
        signoff="Freight Desk",
        tone="formal",
    )

    adjusted = apply_customer_profile(draft, profile)

    assert adjusted.email_body.startswith("Hello Acme team,")
    assert adjusted.email_body.endswith("Freight Desk")
    assert draft.email_body.startswith("Hello,")
    assert draft.email_body.endswith("OpsControl Operations")


def test_unknown_customer_uses_default_profile():
    profile = resolve_customer_profile("missing", {})

    assert profile.customer_id == "default"
    assert profile.preferred_channel == "email"


def test_customer_profile_rejects_unsupported_channel():
    with pytest.raises(ValueError):
        CustomerProfile(customer_id="customer-1", preferred_channel="fax")


# ---- feedback -----------------------------------------------------------

def test_feedback_rejects_unknown_outcome():
    desk = Desk()
    record = make_approval_record(desk)

    with pytest.raises(ValueError):
        record_feedback(desk, record.id, "automatic_send")


def test_feedback_rejects_unknown_exception():
    with pytest.raises(KeyError):
        record_feedback(Desk(), 999, "approved")
