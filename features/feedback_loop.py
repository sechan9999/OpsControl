from dataclasses import dataclass
from datetime import datetime, timezone

from opscontrol.store import Desk

VALID_OUTCOMES = {"approved", "sent_to_review", "dismissed", "corrected"}


@dataclass(frozen=True)
class FeedbackEvent:
    exception_id: int
    outcome: str
    note: str
    created_at: str


def calculate_rlhf_confidence_calibration(exc_type: str, desk: Desk) -> float:
    """Calculate RLHF confidence calibration delta based on operator approval feedback history."""
    dataset = getattr(desk, "feedback_dataset", [])
    type_events = [e for e in dataset if e.get("type") == exc_type]
    if not type_events:
        return 0.0

    approved_count = sum(1 for e in type_events if e.get("outcome") == "approved")
    approval_rate = approved_count / len(type_events)
    # If approval rate > 80%, boost confidence up to +0.08. If < 50%, reduce confidence up to -0.10
    delta = (approval_rate - 0.70) * 0.25
    return round(max(-0.10, min(0.08, delta)), 2)


def record_feedback(
    desk: Desk,
    exception_id: int,
    outcome: str,
    note: str = "",
) -> FeedbackEvent:
    """Record an operator outcome in the existing activity audit trail and update adaptive thresholds."""
    if exception_id not in desk.exceptions:
        raise KeyError(f"unknown exception {exception_id}")

    if outcome not in VALID_OUTCOMES:
        allowed = ", ".join(sorted(VALID_OUTCOMES))
        raise ValueError(f"unsupported feedback outcome '{outcome}'; expected: {allowed}")

    record = desk.exceptions[exception_id]
    exc_type = record.triage.exception_type

    # Append to desk.feedback_dataset for RLHF model calibration
    if not hasattr(desk, "feedback_dataset"):
        desk.feedback_dataset = []
    desk.feedback_dataset.append({
        "id": exception_id,
        "type": exc_type,
        "outcome": outcome,
        "note": note,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })

    # Adaptive threshold adjustment logic
    adjusted_threshold = None
    if outcome == "approved" and record.status == "needs_human_review":
        adjusted_threshold = desk.adjust_threshold(exc_type, -0.05)
    elif outcome == "sent_to_review":
        adjusted_threshold = desk.adjust_threshold(exc_type, 0.05)

    event = FeedbackEvent(
        exception_id=exception_id,
        outcome=outcome,
        note=note.strip(),
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )

    log_kw = {
        "id": event.exception_id,
        "outcome": event.outcome,
        "note": event.note or "-",
    }
    if adjusted_threshold is not None:
        log_kw["adaptive_delta"] = f"{exc_type}:{adjusted_threshold:+.2f}"

    desk.log("info", "operator_feedback", **log_kw)

    return event
