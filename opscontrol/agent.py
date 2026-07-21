from typing import List
from .config import Settings
from .models import Assessment, MitigationAction, TriageResult
from . import tools

RECOMMENDED_ACTIONS = {
    "PORT_DELAY": [
        MitigationAction(
            action_type="REROUTE",
            description="Reroute via inland rail spur or alternate terminal gate to bypass dwell backlog.",
            estimated_cost_usd=1200.0,
            lead_time_saved_days=1.5,
        ),
        MitigationAction(
            action_type="EXPEDITE_SHIPMENT",
            description="Request priority gate pull and dedicated drayage transport.",
            estimated_cost_usd=800.0,
            lead_time_saved_days=1.0,
        ),
        MitigationAction(
            action_type="CUSTOMER_COMMUNICATION",
            description="Notify consignee with updated ETA and proactive OTIF mitigation plan.",
            estimated_cost_usd=0.0,
            lead_time_saved_days=0.0,
        ),
    ],
    "CUSTOMS_HOLD": [
        MitigationAction(
            action_type="CUSTOMS_EXPEDITE",
            description="File priority documentation review and submit customs broker exam request.",
            estimated_cost_usd=450.0,
            lead_time_saved_days=2.0,
        ),
        MitigationAction(
            action_type="CUSTOMER_COMMUNICATION",
            description="Notify customer of exam hold status and revised delivery window.",
            estimated_cost_usd=0.0,
            lead_time_saved_days=0.0,
        ),
    ],
    "REEFER_TEMP": [
        MitigationAction(
            action_type="ACTIVATE_ALTERNATIVE_CARRIER",
            description="Dispatch emergency reefer technician and swap load to temperature-controlled carrier.",
            estimated_cost_usd=2500.0,
            lead_time_saved_days=3.0,
        ),
        MitigationAction(
            action_type="EXPEDITE_SHIPMENT",
            description="Expedite hot-shot transport to nearest cold-storage warehouse.",
            estimated_cost_usd=1500.0,
            lead_time_saved_days=1.5,
        ),
        MitigationAction(
            action_type="ESCALATE_TO_REVIEW",
            description="Flag pharma/perishable product team for cargo insurance audit.",
            estimated_cost_usd=0.0,
            lead_time_saved_days=0.0,
        ),
    ],
    "VESSEL_ROLLOVER": [
        MitigationAction(
            action_type="ACTIVATE_ALTERNATIVE_CARRIER",
            description="Rebook priority container slot on next express sailing.",
            estimated_cost_usd=1800.0,
            lead_time_saved_days=4.0,
        ),
        MitigationAction(
            action_type="CUSTOMER_COMMUNICATION",
            description="Alert consignee of revised ETD and updated vessel voyage number.",
            estimated_cost_usd=0.0,
            lead_time_saved_days=0.0,
        ),
    ],
    "CHASSIS_SHORTAGE": [
        MitigationAction(
            action_type="ACTIVATE_ALTERNATIVE_CARRIER",
            description="Swap to premium drayage partner with committed private chassis fleet.",
            estimated_cost_usd=600.0,
            lead_time_saved_days=1.0,
        ),
    ],
    "WEATHER_DIVERT": [
        MitigationAction(
            action_type="REROUTE",
            description="Cross-dock at alternate regional hub and split priority order portion.",
            estimated_cost_usd=1400.0,
            lead_time_saved_days=2.0,
        ),
    ],
    "ACCIDENT": [
        MitigationAction(
            action_type="EXPEDITE_SHIPMENT",
            description="Arrange recovery tow, container integrity inspection, and replacement trailer.",
            estimated_cost_usd=3200.0,
            lead_time_saved_days=2.0,
        ),
    ],
    "MISSED_CUTOFF": [
        MitigationAction(
            action_type="EXPEDITE_SHIPMENT",
            description="Pay late-gate exception fee or rebook first available feeder vessel.",
            estimated_cost_usd=750.0,
            lead_time_saved_days=1.0,
        ),
    ],
    "GEOPOLITICAL": [
        MitigationAction(
            action_type="ACTIVATE_ALTERNATIVE_CARRIER",
            description="Reroute trade corridor away from restricted zone to pre-qualified secondary carrier.",
            estimated_cost_usd=4000.0,
            lead_time_saved_days=5.0,
        ),
        MitigationAction(
            action_type="ESCALATE_TO_REVIEW",
            description="Escalate trade compliance and risk management team for contract review.",
            estimated_cost_usd=0.0,
            lead_time_saved_days=0.0,
        ),
    ],
    "CYBER_ATTACK": [
        MitigationAction(
            action_type="ESCALATE_TO_REVIEW",
            description="Initiate manual bill of lading fallback procedure and system audit.",
            estimated_cost_usd=0.0,
            lead_time_saved_days=1.0,
        ),
        MitigationAction(
            action_type="CUSTOMER_COMMUNICATION",
            description="Send manual status verification report to customer security team.",
            estimated_cost_usd=0.0,
            lead_time_saved_days=0.0,
        ),
    ],
    "FINANCIAL_FAILURE": [
        MitigationAction(
            action_type="ACTIVATE_ALTERNATIVE_CARRIER",
            description="Transfer active freight custody to backup carrier under emergency contract terms.",
            estimated_cost_usd=3500.0,
            lead_time_saved_days=4.0,
        ),
    ],
    "PANDEMIC": [
        MitigationAction(
            action_type="INCREASE_SAFETY_STOCK",
            description="Authorize safety stock buffer pull from regional distribution node.",
            estimated_cost_usd=2000.0,
            lead_time_saved_days=3.0,
        ),
    ],
    "UNKNOWN": [
        MitigationAction(
            action_type="ESCALATE_TO_REVIEW",
            description="Route to human operations queue for manual assessment.",
            estimated_cost_usd=0.0,
            lead_time_saved_days=0.0,
        ),
    ],
}


def _get_mitigation_actions(t: TriageResult, lane: str | None) -> List[MitigationAction]:
    base_actions = RECOMMENDED_ACTIONS.get(t.exception_type, RECOMMENDED_ACTIONS["UNKNOWN"])
    actions = list(base_actions)
    if lane and t.exception_type in ("PORT_DELAY", "REEFER_TEMP", "VESSEL_ROLLOVER", "GEOPOLITICAL", "FINANCIAL_FAILURE"):
        alts = tools.alternative_carriers(lane)
        if alts:
            best_alt = alts[0]
            alt_action = MitigationAction(
                action_type="ACTIVATE_ALTERNATIVE_CARRIER",
                description=f"Activate pre-qualified backup carrier '{best_alt.name}' ({best_alt.capacity_available}, +{best_alt.price_premium_pct}% cost).",
                estimated_cost_usd=1500.0,
                lead_time_saved_days=float(best_alt.estimated_transit_days or 2),
            )
            # Insert at top if not already primary
            if not any(a.action_type == "ACTIVATE_ALTERNATIVE_CARRIER" for a in actions[:1]):
                actions.insert(0, alt_action)
    return actions


def investigate(t: TriageResult, settings: Settings) -> Assessment:
    """Bounded investigation loop mirroring SPEC section 4b, with a deterministic
    tool-selection policy standing in for GPT-5.6 reasoning. Tool errors become
    trace entries, never exceptions; exhaustion caps confidence at 0.5."""
    trace = []
    shipment = None
    conditions = None
    impact = None
    delay_hours = t.delay_hours

    rounds = 0
    for rounds in range(1, settings.max_rounds + 1):
        if shipment is None:
            result = tools.lookup_shipment(t.shipment_ref)
            trace.append({"round": rounds, "tool": "lookup_shipment",
                          "args": {"ref": t.shipment_ref}, "result": result})
            if "error" not in result:
                shipment = result
            elif rounds >= 3:
                break  # can't identify the shipment; stop retrying
            continue
        if t.location and conditions is None:
            result = tools.port_conditions(t.location)
            trace.append({"round": rounds, "tool": "port_conditions",
                          "args": {"location": t.location}, "result": result})
            conditions = result
            if delay_hours is None and "error" not in result:
                delay_hours = float(result.get("avg_dwell_hours", 0))
            continue
        if impact is None:
            if delay_hours is None:
                delay_hours = 12.0  # conservative default when nothing states a delay
            result = tools.eta_impact(t.shipment_ref, delay_hours, shipment["slack_hours"])
            trace.append({"round": rounds, "tool": "eta_impact",
                          "args": {"ref": t.shipment_ref, "delay_hours": delay_hours},
                          "result": result})
            impact = result
            continue
        break  # everything gathered before exhausting rounds

    window_missed = bool(impact and impact.get("window_missed"))
    affected_value = float(shipment["order_value_usd"]) if (shipment and window_missed) else 0.0

    # Calculate time to impact in days
    time_to_impact_days = None
    if shipment and "slack_hours" in shipment:
        slack = float(shipment["slack_hours"])
        delay = float(delay_hours or 0.0)
        remaining_hours = max(0.0, slack - delay)
        time_to_impact_days = round(remaining_hours / 24.0, 1)

    # confidence: how complete is the picture we assembled?
    confidence = 0.92
    if shipment is None:
        confidence -= 0.45
    if t.shipment_ref is None:
        confidence -= 0.10
    if t.exception_type == "UNKNOWN":
        confidence -= 0.25
    if t.location is None:
        confidence -= 0.08
    if t.delay_hours is None and impact is not None:
        confidence -= 0.10  # delay was inferred, not stated
    if rounds >= settings.max_rounds and impact is None:
        confidence = min(confidence, 0.5)  # exhaustion cap (SPEC 4b)
    confidence = round(max(0.05, min(1.0, confidence)), 2)

    confidence_label = "High" if confidence >= 0.85 else ("Medium" if confidence >= 0.60 else "Low")

    lane = shipment.get("lane") if shipment else None
    mitigation_actions = _get_mitigation_actions(t, lane)
    primary_recommended = mitigation_actions[0].description if mitigation_actions else "Route to operations for manual review."

    if shipment is None:
        summary = (f"Could not identify shipment for '{t.summary[:60]}'; "
                   f"investigation stopped after {rounds} rounds.")
    else:
        parts = [f"{shipment['commodity']} via {shipment['carrier']} ({shipment['lane']})"]
        if window_missed:
            parts.append(f"delivery window MISSED by {impact['hours_past_window']}h; "
                         f"${affected_value:,.0f} at risk")
        elif impact:
            parts.append(f"delay {impact['delay_hours']:.0f}h absorbed by "
                         f"{shipment['slack_hours']}h slack; window holds")
        if conditions and "error" not in conditions:
            parts.append(f"port: {conditions['congestion_level']} congestion, {conditions['weather']}")
        summary = " | ".join(parts)

    return Assessment(
        impact_summary=summary,
        window_missed=window_missed,
        affected_value=affected_value,
        confidence=confidence,
        recommended_action=primary_recommended,
        rounds_used=rounds,
        trace=trace,
        time_to_impact_days=time_to_impact_days,
        confidence_label=confidence_label,
        mitigation_actions=mitigation_actions,
    )
