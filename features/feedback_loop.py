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

    # Adaptive threshold adjustment logic:
    # - Approved from human review -> threshold -0.05 (confidence/trust goes up, easier auto-queue)
    # - Sent to human review (demoted) -> threshold +0.05 (confidence/trust goes down, stricter auto-queue)
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
