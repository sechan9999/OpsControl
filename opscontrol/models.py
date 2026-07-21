from dataclasses import dataclass, field
from typing import Optional

EXCEPTION_TYPES = [
    "PORT_DELAY", "CUSTOMS_HOLD", "VESSEL_ROLLOVER", "CHASSIS_SHORTAGE",
    "WEATHER_DIVERT", "REEFER_TEMP", "ACCIDENT", "MISSED_CUTOFF", "UNKNOWN",
]

STATUSES = [
    "triaged", "investigating", "drafting",
    "ready_for_approval", "needs_human_review", "sent", "dismissed",
]

TIERS = ["red", "orange", "green"]


@dataclass
class TriageResult:
    shipment_ref: Optional[str]
    exception_type: str
    location: Optional[str]
    severity: int                     # 1..5
    summary: str
    customer_impact: str
    delay_hours: Optional[float] = None


@dataclass
class Assessment:
    impact_summary: str
    window_missed: bool
    affected_value: float
    confidence: float                 # 0..1
    recommended_action: str
    rounds_used: int
    trace: list = field(default_factory=list)   # [{round, tool, args, result}]


@dataclass(frozen=True)
class Draft:
    email_subject: str
    email_body: str
    action_plan: str



@dataclass
class ExceptionRecord:
    id: int
    message_id: int
    raw: str
    channel: str
    triage: TriageResult
    tier: str = "green"
    status: str = "triaged"
    assessment: Optional[Assessment] = None
    draft: Optional[Draft] = None
    created_at: str = ""
