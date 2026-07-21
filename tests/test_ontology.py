"""Unit tests for Microsoft Supply Chain Disruption Ontology integrations in OpsControl.

Tests new disruption types (GEOPOLITICAL, CYBER_ATTACK, FINANCIAL_FAILURE, PANDEMIC),
severity labels (Critical/High/Medium/Low), time_to_impact_days, confidence labels,
MitigationAction objects, and AlternativeCarrier tools.
"""
from opscontrol.config import Settings
from opscontrol.models import AlternativeCarrier, MitigationAction
from opscontrol.pipeline import process_message
from opscontrol.store import Desk
from opscontrol.tools import MockShipmentAdapter, alternative_carriers
from opscontrol.triage import stub_triage

SETTINGS = Settings()


def test_triage_geopolitical_disruption():
    raw = "ALERT: Port closure and dockworker strike at Port of Savannah. Sanctions imposed affecting OPS-40021-A."
    t = stub_triage(raw, "email")
    assert t.exception_type == "GEOPOLITICAL"
    assert t.severity_label in ("High", "Critical")
    assert t.shipment_ref == "OPS-40021-A"


def test_triage_cyber_attack_disruption():
    raw = "SYSTEM OUTAGE: Ransomware cyber attack hit carrier TMS. Gate operations suspended for OPS-40026-C."
    t = stub_triage(raw, "edi")
    assert t.exception_type == "CYBER_ATTACK"
    assert t.severity_label in ("High", "Critical")
    assert t.shipment_ref == "OPS-40026-C"


def test_triage_financial_failure_disruption():
    raw = "Carrier bankruptcy filed for EverLine freight lines. Payment stop issued."
    t = stub_triage(raw, "email")
    assert t.exception_type == "FINANCIAL_FAILURE"
    assert t.severity_label in ("High", "Critical")


def test_triage_pandemic_disruption():
    raw = "Quarantine health emergency and facility closure at warehouse port node."
    t = stub_triage(raw, "email")
    assert t.exception_type == "PANDEMIC"


def test_pipeline_generates_mitigation_actions_and_time_to_impact():
    desk = Desk()
    msg = (
        "Escalation: OPS-40045-A is temperature-sensitive pharma with a hard delivery "
        "window Thursday 08:00-12:00. Current Savannah hold puts arrival at Thursday 15:40. "
        "Client contract has a $25k OTIF penalty clause."
    )
    rec = process_message(msg, "email", desk, SETTINGS)
    assert rec is not None
    assert rec.assessment is not None

    a = rec.assessment
    assert isinstance(a.mitigation_actions, list)
    assert len(a.mitigation_actions) >= 1
    assert isinstance(a.mitigation_actions[0], MitigationAction)
    assert a.confidence_label in ("High", "Medium", "Low")
    assert a.time_to_impact_days is not None


def test_alternative_carrier_lookup():
    alts = alternative_carriers("SAV->RDU")
    assert len(alts) >= 1
    assert isinstance(alts[0], AlternativeCarrier)
    assert alts[0].name == "ColdExpress"
    assert alts[0].qualification_status == "approved"
    assert alts[0].price_premium_pct == 8.0
