from .models import Assessment, Draft, TriageResult

TYPE_LABEL = {
    "PORT_DELAY": "a port delay", "CUSTOMS_HOLD": "a customs hold",
    "VESSEL_ROLLOVER": "a vessel schedule change", "CHASSIS_SHORTAGE": "an equipment shortage",
    "WEATHER_DIVERT": "a weather-related reroute", "REEFER_TEMP": "a refrigeration issue",
    "ACCIDENT": "a transit incident", "MISSED_CUTOFF": "a missed documentation cutoff",
    "UNKNOWN": "an operational exception",
}


def compose(t: TriageResult, a: Assessment) -> Draft:
    ref = t.shipment_ref or "your shipment"
    label = TYPE_LABEL[t.exception_type]
    subject = f"Update on {ref}: {label} at {t.location}" if t.location \
        else f"Update on {ref}: {label}"

    lines = [
        f"Hello,",
        "",
        f"We want to keep you informed: {ref} is affected by {label}"
        + (f" at {t.location}." if t.location else "."),
    ]
    if a.window_missed:
        lines.append(
            "Our assessment shows the scheduled delivery window is at risk. "
            "We are already acting on a mitigation plan and will confirm a revised "
            "delivery time within the next update."
        )
    elif t.delay_hours:
        lines.append(
            f"Current estimates indicate a delay of about {t.delay_hours:.0f} hours, "
            "which we expect to absorb within the planned schedule."
        )
    else:
        lines.append("At this time we do not expect an impact to your delivery schedule.")
    lines += [
        f"Next step on our side: {a.recommended_action}",
        "",
        "We will follow up as soon as there is a material update. Thank you for your patience.",
        "",
        "OpsControl Operations",
    ]

    plan = "\n".join([
        f"- {a.recommended_action}",
        f"- Impact: {a.impact_summary}",
        f"- Confidence: {a.confidence:.2f} ({a.rounds_used} investigation rounds)",
        "- Update customer after mitigation is confirmed",
    ])

    return Draft(email_subject=subject, email_body="\n".join(lines), action_plan=plan)
