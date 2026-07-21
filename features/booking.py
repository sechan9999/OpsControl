import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from opscontrol.models import AlternativeCarrier, MitigationAction
from opscontrol.store import Desk
from opscontrol.tools import alternative_carriers


@dataclass(frozen=True)
class TenderBookingReceipt:
    booking_id: str
    carrier_name: str
    lane: str
    estimated_cost_usd: float
    confirmed_at: str
    status: str  # confirmed, in_progress, completed


def execute_alternative_carrier_booking(
    desk: Desk,
    exception_id: int,
    carrier: AlternativeCarrier,
    operator_name: str = "Operator",
) -> TenderBookingReceipt:
    """Execute automated tender booking for an approved alternative carrier."""
    if exception_id not in desk.exceptions:
        raise KeyError(f"unknown exception {exception_id}")

    record = desk.exceptions[exception_id]
    h = int(hashlib.md5(f"{exception_id}-{carrier.name}".encode()).hexdigest(), 16)
    booking_id = f"BK-2026-{h % 8999 + 1000}"
    cost = float(record.assessment.affected_value * (carrier.price_premium_pct or 10.0) / 100.0) if record.assessment else 1200.0
    cost = max(800.0, cost)

    receipt = TenderBookingReceipt(
        booking_id=booking_id,
        carrier_name=carrier.name,
        lane=carrier.lane,
        estimated_cost_usd=round(cost, 2),
        confirmed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        status="confirmed",
    )

    # Update record mitigation action status
    if record.assessment and record.assessment.mitigation_actions:
        updated_actions = []
        for act in record.assessment.mitigation_actions:
            if act.action_type == "ACTIVATE_ALTERNATIVE_CARRIER":
                updated_actions.append(MitigationAction(
                    action_type=act.action_type,
                    description=f"Active Tender #{booking_id}: {carrier.name} ({carrier.capacity_available}, confirmed).",
                    estimated_cost_usd=receipt.estimated_cost_usd,
                    lead_time_saved_days=act.lead_time_saved_days,
                    status="in_progress",
                ))
            else:
                updated_actions.append(act)
        record.assessment.mitigation_actions = updated_actions

    desk.log(
        "info",
        "carrier_tender_executed",
        id=exception_id,
        ref=record.triage.shipment_ref or "-",
        booking_id=booking_id,
        carrier=carrier.name,
        cost=f"${receipt.estimated_cost_usd:,.0f}",
        by=operator_name,
    )

    return receipt
