from dataclasses import dataclass, field
from typing import Optional

EXCEPTION_TYPES = [
    "PORT_DELAY", "CUSTOMS_HOLD", "VESSEL_ROLLOVER", "CHASSIS_SHORTAGE",
    "WEATHER_DIVERT", "REEFER_TEMP", "ACCIDENT", "MISSED_CUTOFF",
    "GEOPOLITICAL", "CYBER_ATTACK", "FINANCIAL_FAILURE", "PANDEMIC", "UNKNOWN",
]

STATUSES = [
    "triaged", "investigating", "drafting",
    "ready_for_approval", "needs_human_review", "sent", "dismissed",
]

TIERS = ["red", "orange", "green"]


@dataclass(frozen=True)
class MitigationAction:
    action_type: str  # ACTIVATE_ALTERNATIVE_CARRIER, EXPEDITE_SHIPMENT, REROUTE, CUSTOMS_EXPEDITE, INCREASE_SAFETY_STOCK, CUSTOMER_COMMUNICATION, ESCALATE_TO_REVIEW
    description: str
    estimated_cost_usd: Optional[float] = None
    lead_time_saved_days: Optional[float] = None
    status: str = "proposed"  # proposed, approved, in_progress, completed, cancelled


@dataclass(frozen=True)
class AlternativeCarrier:
    name: str
    lane: str
    qualification_status: str  # approved, pre_qualified, pending
    capacity_available: Optional[str] = None
    price_premium_pct: Optional[float] = None
    estimated_transit_days: Optional[int] = None


@dataclass
class TriageResult:
    shipment_ref: Optional[str]
    exception_type: str
    location: Optional[str]
    severity: int                     # 1..5
    summary: str
    customer_impact: str
    delay_hours: Optional[float] = None
    severity_label: str = "Medium"     # Critical, High, Medium, Low
    estimated_duration_days: Optional[int] = None


@dataclass
class Assessment:
    impact_summary: str
    window_missed: bool
    affected_value: float
    confidence: float                 # 0..1
    recommended_action: str
    rounds_used: int
    trace: list = field(default_factory=list)   # [{round, tool, args, result}]
    time_to_impact_days: Optional[float] = None
    confidence_label: str = "Medium"   # High, Medium, Low
    mitigation_actions: list[MitigationAction] = field(default_factory=list)


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
