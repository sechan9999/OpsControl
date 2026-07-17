from .config import Settings
from .models import Assessment, TriageResult
from . import tools

RECOMMENDED = {
    "PORT_DELAY": "Reroute via inland rail spur or hold for gate reopen; confirm revised ETA with carrier.",
    "CUSTOMS_HOLD": "File expedited clearance; hold the delivery appointment.",
    "VESSEL_ROLLOVER": "Rebook on next sailing; flag OTIF risk to customer service.",
    "CHASSIS_SHORTAGE": "Swap to expedited drayage partner with committed capacity.",
    "WEATHER_DIVERT": "Cross-dock at alternate hub; split priority portion of the order.",
    "REEFER_TEMP": "Dispatch reefer tech; prepare cold-chain contingency and quality hold.",
    "ACCIDENT": "Arrange tow and container inspection; reschedule final-mile delivery.",
    "MISSED_CUTOFF": "Confirm auto-rebooking; notify consignee of revised ETD.",
    "UNKNOWN": "Route to operations for manual classification.",
}


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
        recommended_action=RECOMMENDED[t.exception_type],
        rounds_used=rounds,
        trace=trace,
    )
