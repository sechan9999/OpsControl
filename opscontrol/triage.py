import re
from typing import Optional

from .config import Settings
from .models import TriageResult

REF_RE = re.compile(r"OPS-\d{5}-[A-Z]", re.IGNORECASE)
HOURS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:hr|hrs|hours|h\b)", re.IGNORECASE)
DAYS_RE = re.compile(r"\+?\s*(\d+)\s*d(?:ays?)?\b", re.IGNORECASE)

KNOWN_LOCATIONS = [
    "Port of Savannah", "Savannah", "Long Beach", "Rotterdam", "Busan New Port",
    "Busan", "Singapore", "Memphis", "Norfolk Intl", "Norfolk", "Charleston",
]

# order matters: most specific signals first
TYPE_RULES = [
    ("REEFER_TEMP", ["reefer", "genset", "setpoint", "temperature-sensitive"]),
    ("CUSTOMS_HOLD", ["customs", "vacis", "clearance", "documentation review", "x-ray", "xray", "exam"]),
    ("VESSEL_ROLLOVER", ["rollover", "rolled to next sailing", "schedule change"]),
    ("CHASSIS_SHORTAGE", ["chassis"]),
    ("WEATHER_DIVERT", ["divert", "rerouted", "reroute"]),
    ("ACCIDENT", ["accident", "tow required"]),
    ("MISSED_CUTOFF", ["missed the documentation cutoff", "missed erd", "erd cutoff", "cutoff"]),
    ("GEOPOLITICAL", ["sanctions", "trade war", "embargo", "port closure", "strike"]),
    ("CYBER_ATTACK", ["cyber", "ransomware", "system outage", "it failure", "hack"]),
    ("FINANCIAL_FAILURE", ["bankruptcy", "receivership", "credit hold", "payment stop"]),
    ("PANDEMIC", ["quarantine", "health emergency", "outbreak", "facility closure"]),
    ("PORT_DELAY", ["held", "gate closed", "gate moves", "congestion", "berth", "backlog",
                    "delay", "delayed", "detention", "waiting", "appointment window was missed",
                    "demurrage", "12h behind", "running", "suspended"]),
]

INFORMATIONAL = ["released", "gate out completed", "no action needed", "easing",
                 "clearing", "clock paused", "reopen"]

ESCALATION_WORDS = ["penalty", "pharma", "escalation", "hard delivery window", "urgent"]


NEGATION_PATTERNS = re.compile(
    r"\b(no|not|without|cleared?|resolved?|cancel+ed?|lifted?|easing|eased)"
    r"\s+\w*(\s+\w+){0,3}\s*",
    re.IGNORECASE,
)


def _looks_malformed(raw: str) -> bool:
    if len(raw.encode()) < 10:
        return True
    words = re.findall(r"[A-Za-z]{2,}", raw)
    has_alphanum_pair = bool(re.search(r"[A-Za-z][0-9]|[0-9][A-Za-z]", raw))
    clearly_corrupted = "@@" in raw or re.search(r"0x[0-9a-fA-F]{2,}", raw)
    return len(words) < 3 and not has_alphanum_pair or bool(clearly_corrupted)


def _parse_delay_hours(raw: str) -> Optional[float]:
    m = HOURS_RE.search(raw)
    if m:
        return float(m.group(1))
    m = DAYS_RE.search(raw)
    if m:
        return float(m.group(1)) * 24
    return None


def _severity_label(severity: int) -> str:
    if severity >= 5:
        return "Critical"
    if severity == 4:
        return "High"
    if severity == 3:
        return "Medium"
    return "Low"


def _parse_duration_days(raw: str, delay_hours: Optional[float]) -> Optional[int]:
    m = DAYS_RE.search(raw)
    if m:
        return int(m.group(1))
    if delay_hours:
        days = round(delay_hours / 24)
        return max(1, days) if days >= 1 else None
    return None


def _find_location(raw: str) -> Optional[str]:
    low = raw.lower()
    for loc in KNOWN_LOCATIONS:
        if loc.lower() in low:
            return loc
    return None


def _has_negation_near(raw: str, needle: str) -> bool:
    """Return True when a negation word appears within 5 words before ``needle``."""
    low = raw.lower()
    pos = low.find(needle)
    if pos == -1:
        return False
    # examine the 60 characters before the keyword
    window = low[max(0, pos - 60) : pos]
    return bool(NEGATION_PATTERNS.search(window))


def _classify(raw: str) -> str:
    low = raw.lower()
    for exc_type, needles in TYPE_RULES:
        for needle in needles:
            if needle in low and not _has_negation_near(raw, needle):
                return exc_type
    return "UNKNOWN"


def stub_triage(raw: str, channel: str) -> TriageResult:
    """Deterministic stand-in for the GPT-5.6 structured-output triage call.
    Same output contract; zero tokens; reproducible demos."""
    if _looks_malformed(raw):
        return TriageResult(
            shipment_ref=None, exception_type="UNKNOWN", location=None, severity=2,
            summary="Unparseable feed message", customer_impact="Unknown until reviewed",
            severity_label="Low", estimated_duration_days=None,
        )

    low = raw.lower()
    ref_match = REF_RE.search(raw)
    ref = ref_match.group(0).upper() if ref_match else None
    exc_type = _classify(raw)
    location = _find_location(raw)
    delay_hours = _parse_delay_hours(raw)
    duration_days = _parse_duration_days(raw, delay_hours)
    informational = any(n in low for n in INFORMATIONAL) and exc_type in ("PORT_DELAY", "UNKNOWN")

    base = {
        "REEFER_TEMP": 4, "GEOPOLITICAL": 4, "CYBER_ATTACK": 4, "FINANCIAL_FAILURE": 4,
        "CUSTOMS_HOLD": 3, "VESSEL_ROLLOVER": 3, "ACCIDENT": 3, "PANDEMIC": 3,
        "MISSED_CUTOFF": 3, "CHASSIS_SHORTAGE": 2, "WEATHER_DIVERT": 3,
        "PORT_DELAY": 2, "UNKNOWN": 2,
    }[exc_type]
    severity = base
    if any(w in low for w in ESCALATION_WORDS):
        severity += 2
    if delay_hours and delay_hours >= 24:
        severity += 1
    if informational:
        severity = 1
    severity = max(1, min(5, severity))
    sev_label = _severity_label(severity)

    summary = raw.strip().replace("\n", " ")
    summary = (summary[:140] + "...") if len(summary) > 140 else summary
    impact = ("Informational; no customer action expected." if informational
              else f"{exc_type.replace('_', ' ').title()} affecting {ref or 'unidentified shipment'}"
                   + (f", est. delay {delay_hours:.0f}h" if delay_hours else ""))

    return TriageResult(
        shipment_ref=ref, exception_type=exc_type, location=location,
        severity=severity, summary=summary, customer_impact=impact,
        delay_hours=delay_hours, severity_label=sev_label,
        estimated_duration_days=duration_days,
    )


def _openai_triage(raw: str, channel: str, settings: Settings) -> TriageResult:
    """Experimental real-LLM path (OPSCONTROL_USE_OPENAI=1 + OPENAI_API_KEY).
    Falls back to the stub on any failure - triage never raises."""
    import json

    from openai import OpenAI

    schema = {
        "type": "object", "additionalProperties": False,
        "required": ["shipment_ref", "exception_type", "location", "severity",
                     "summary", "customer_impact", "delay_hours", "severity_label", "estimated_duration_days"],
        "properties": {
            "shipment_ref": {"type": ["string", "null"]},
            "exception_type": {"type": "string", "enum": [
                "PORT_DELAY", "CUSTOMS_HOLD", "VESSEL_ROLLOVER", "CHASSIS_SHORTAGE",
                "WEATHER_DIVERT", "REEFER_TEMP", "ACCIDENT", "MISSED_CUTOFF",
                "GEOPOLITICAL", "CYBER_ATTACK", "FINANCIAL_FAILURE", "PANDEMIC", "UNKNOWN"]},
            "location": {"type": ["string", "null"]},
            "severity": {"type": "integer", "minimum": 1, "maximum": 5},
            "summary": {"type": "string"},
            "customer_impact": {"type": "string"},
            "delay_hours": {"type": ["number", "null"]},
            "severity_label": {"type": "string", "enum": ["Critical", "High", "Medium", "Low"]},
            "estimated_duration_days": {"type": ["integer", "null"]},
        },
    }
    client = OpenAI()
    rsp = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": "You triage raw freight carrier messages into structured exceptions."},
            {"role": "user", "content": f"channel={channel}\n{raw}"},
        ],
        response_format={"type": "json_schema",
                         "json_schema": {"name": "triage_result", "strict": True, "schema": schema}},
    )
    data = json.loads(rsp.choices[0].message.content)
    return TriageResult(**data)


def triage(raw: str, channel: str, settings: Settings) -> TriageResult:
    if settings.use_openai:
        try:
            return _openai_triage(raw, channel, settings)
        except Exception:
            pass  # never let triage raise; stub is the safety net
    return stub_triage(raw, channel)
