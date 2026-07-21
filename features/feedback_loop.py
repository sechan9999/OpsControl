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
    """Record an operator outcome in the existing activity audit trail."""
    if exception_id not in desk.exceptions:
        raise KeyError(f"unknown exception {exception_id}")

    if outcome not in VALID_OUTCOMES:
        allowed = ", ".join(sorted(VALID_OUTCOMES))
        raise ValueError(f"unsupported feedback outcome '{outcome}'; expected: {allowed}")

    event = FeedbackEvent(
        exception_id=exception_id,
        outcome=outcome,
        note=note.strip(),
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )

    desk.log(
        "info",
        "operator_feedback",
        id=event.exception_id,
        outcome=event.outcome,
        note=event.note or "-",
    )

    return event
