from dataclasses import dataclass
from typing import Optional

from .models import Assessment, Draft, TriageResult

TYPE_LABEL = {
    "PORT_DELAY": "a port delay",
    "CUSTOMS_HOLD": "a customs hold",
    "VESSEL_ROLLOVER": "a vessel schedule change",
    "CHASSIS_SHORTAGE": "an equipment shortage",
    "WEATHER_DIVERT": "a weather-related reroute",
    "REEFER_TEMP": "a refrigeration issue",
    "ACCIDENT": "a transit incident",
    "MISSED_CUTOFF": "a missed documentation cutoff",
    "GEOPOLITICAL": "a geopolitical disruption",
    "CYBER_ATTACK": "an IT system disruption",
    "FINANCIAL_FAILURE": "a carrier financial disruption",
    "PANDEMIC": "a health emergency facility closure",
    "UNKNOWN": "an operational exception",
}


@dataclass
class DraftTemplate:
    """Structured email template — sections are kept separate so downstream
    transformations (e.g. customer-profile application) can target each part
    without fragile ``startswith`` / ``endswith`` string matching."""

    greeting: str
    location_clause: str
    situation_line: str
    next_step_line: str
    closing: str
    signoff: str

    def render_body(self) -> str:
        return "\n".join([
            self.greeting,
            "",
            self.location_clause,
            self.situation_line,
            self.next_step_line,
            "",
            self.closing,
            "",
            self.signoff,
        ])


def build_template(
    t: TriageResult,
    a: Assessment,
    greeting: str = "Hello,",
    signoff: str = "OpsControl Operations",
) -> DraftTemplate:
    ref = t.shipment_ref or "your shipment"
    label = TYPE_LABEL.get(t.exception_type, "an operational exception")
    loc_clause = (
        f"We want to keep you informed: {ref} is affected by {label} at {t.location}."
        if t.location
        else f"We want to keep you informed: {ref} is affected by {label}."
    )

    if a.window_missed:
        situation = (
            "Our assessment shows the scheduled delivery window is at risk. "
            "We are already acting on a mitigation plan and will confirm a revised "
            "delivery time within the next update."
        )
    elif a.time_to_impact_days is not None and a.time_to_impact_days > 0:
        situation = (
            f"Current estimates indicate an estimated buffer of {a.time_to_impact_days:.1f} days "
            "before scheduled delivery, which we expect to maintain."
        )
    elif t.delay_hours:
        situation = (
            f"Current estimates indicate a delay of about {t.delay_hours:.0f} hours, "
            "which we expect to absorb within the planned schedule."
        )
    else:
        situation = "At this time we do not expect an impact to your delivery schedule."

    return DraftTemplate(
        greeting=greeting,
        location_clause=loc_clause,
        situation_line=situation,
        next_step_line=f"Next step on our side: {a.recommended_action}",
        closing="We will follow up as soon as there is a material update. Thank you for your patience.",
        signoff=signoff,
    )


def compose(
    t: TriageResult,
    a: Assessment,
    greeting: str = "Hello,",
    signoff: str = "OpsControl Operations",
) -> Draft:
    """Compose a customer-ready Draft from triage and assessment results.

    Optional ``greeting`` and ``signoff`` parameters allow caller-supplied
    customer profile values without requiring a separate post-processing step.
    """
    ref = t.shipment_ref or "your shipment"
    label = TYPE_LABEL.get(t.exception_type, "an operational exception")
    subject = (
        f"Update on {ref}: {label} at {t.location}"
        if t.location
        else f"Update on {ref}: {label}"
    )

    template = build_template(t, a, greeting=greeting, signoff=signoff)
    body = template.render_body()

    plan_lines = []
    if a.mitigation_actions:
        plan_lines.append("Mitigation Actions:")
        for act in a.mitigation_actions:
            cost_str = f" (${act.estimated_cost_usd:,.0f})" if act.estimated_cost_usd else ""
            saved_str = f" [save {act.lead_time_saved_days}d]" if act.lead_time_saved_days else ""
            plan_lines.append(f"- [{act.action_type}] {act.description}{cost_str}{saved_str}")
    else:
        plan_lines.append(f"- {a.recommended_action}")

    plan_lines.extend([
        f"- Impact: {a.impact_summary}",
        f"- Confidence: {a.confidence_label} ({a.confidence:.2f}, {a.rounds_used} investigation rounds)",
        "- Update customer after mitigation is confirmed",
    ])

    plan = "\n".join(plan_lines)

    return Draft(email_subject=subject, email_body=body, action_plan=plan)
