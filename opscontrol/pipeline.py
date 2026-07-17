from typing import Optional

from .agent import investigate
from .composer import compose
from .config import Settings
from .models import ExceptionRecord
from .store import Desk
from .tiering import tier
from .triage import triage


def process_message(raw: str, channel: str, desk: Desk,
                    settings: Settings) -> Optional[ExceptionRecord]:
    """One message through the full pipeline. Mirrors SPEC section 1 states.
    Returns the ExceptionRecord, or None when the message was a duplicate.
    Never raises: any unexpected failure routes to needs_human_review."""
    if desk.seen_or_add(raw):
        desk.counters["duplicates"] += 1
        desk.log("warning", "duplicate_suppressed", hash="hit", channel=channel)
        return None

    desk.counters["ingested"] += 1
    t = triage(raw, channel, settings)
    rec = desk.add_exception(raw, channel, t)
    desk.log("info", "exception_received", id=rec.id,
             ref=t.shipment_ref or "-", type=t.exception_type, severity=t.severity)

    try:
        if t.exception_type == "UNKNOWN":
            rec.tier = tier(t.severity, False, 0)
            desk.set_status(rec.id, "needs_human_review")
            desk.log("warning", "routed_to_review", id=rec.id, reason="unclassified")
            return rec

        desk.set_status(rec.id, "investigating")
        desk.log("info", "agent_investigation_started", id=rec.id, ref=t.shipment_ref or "-")
        assessment = investigate(t, settings)
        desk.save_assessment(rec.id, assessment)
        desk.log("info", "agent_investigation_done", id=rec.id,
                 rounds=assessment.rounds_used, confidence=assessment.confidence,
                 window_missed=assessment.window_missed)

        rec.tier = tier(t.severity, assessment.window_missed, assessment.affected_value)

        desk.set_status(rec.id, "drafting")
        desk.save_draft(rec.id, compose(t, assessment))

        if assessment.confidence >= settings.confidence_threshold:
            desk.set_status(rec.id, "ready_for_approval")
            desk.log("info", "draft_ready", id=rec.id, tier=rec.tier)
        else:
            desk.set_status(rec.id, "needs_human_review")
            desk.log("warning", "routed_to_review", id=rec.id,
                     reason=f"confidence {assessment.confidence:.2f} < {settings.confidence_threshold}")
        return rec

    except Exception as e:  # pipeline boundary: never kill the desk
        rec.status = "needs_human_review"
        desk.log("error", "pipeline_failed", id=rec.id, error=str(e))
        return rec
