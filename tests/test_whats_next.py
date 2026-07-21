"""Unit tests for FreightDesk "What's Next" roadmap features.

Tests AIS vessel tracking, Fabric IQ AI Graph Agent queries, One-Click Alternative Carrier Booking,
Enterprise RBAC permissions, SOC2 WORM audit log export, and RLHF confidence calibration.
"""
import pytest

from features.booking import execute_alternative_carrier_booking
from features.feedback_loop import calculate_rlhf_confidence_calibration, record_feedback
from features.rbac import can_user_approve_record, export_soc2_audit_logs_json, get_role_permissions
from opscontrol.config import Settings
from opscontrol.graph_agent import query_fabric_iq_agent
from opscontrol.pipeline import process_message
from opscontrol.store import Desk
from opscontrol.telemetry import get_port_telemetry, get_vessel_telemetry
from opscontrol.tools import AlternativeCarrier

SETTINGS = Settings()


def test_vessel_and_port_telemetry():
    vessel = get_vessel_telemetry("OPS-40045-A")
    assert vessel is not None
    assert vessel.vessel_name == "MV Polar Express"
    assert vessel.status == "Moored"

    port = get_port_telemetry("Port of Savannah")
    assert port is not None
    assert port.code == "USSAV"
    assert port.congestion_index == 0.88


def test_fabric_iq_graph_query_agent():
    desk = Desk()
    process_message("STATUS: CNTR HELD PORT OF SAVANNAH REASON WX", "edi", desk, SETTINGS)

    res = query_fabric_iq_agent("What is our total revenue exposure if the Port of Savannah closes?", desk)
    assert res.affected_nodes >= 1
    assert "Port of Savannah" in res.summary_answer
    assert "MATCH" in res.cypher_query
    assert "graph LR" in res.mermaid_subgraph


def test_one_click_alternative_carrier_booking():
    desk = Desk()
    msg = (
        "Escalation: OPS-40045-A is temperature-sensitive pharma with a hard delivery "
        "window Thursday 08:00-12:00. Current Savannah hold puts arrival at Thursday 15:40."
    )
    rec = process_message(msg, "email", desk, SETTINGS)
    assert rec is not None

    alt_carrier = AlternativeCarrier(
        name="ColdExpress", lane="SAV->RDU", qualification_status="approved",
        capacity_available="12 loads/wk", price_premium_pct=8.0, estimated_transit_days=1,
    )
    receipt = execute_alternative_carrier_booking(desk, rec.id, alt_carrier, operator_name="J. Park")

    assert receipt.booking_id.startswith("BK-2026-")
    assert receipt.carrier_name == "ColdExpress"
    assert receipt.status == "confirmed"
    assert rec.assessment.mitigation_actions[0].status == "in_progress"


def test_enterprise_rbac_permissions():
    op_perms = get_role_permissions("Operator")
    assert op_perms.can_approve_standard is True
    assert op_perms.can_approve_high_value_red is False

    sup_perms = get_role_permissions("Supervisor")
    assert sup_perms.can_approve_high_value_red is True

    # Operator cannot approve RED tier with $25k risk
    assert can_user_approve_record("Operator", "red", 25000.0) is False
    # Supervisor can approve RED tier with $25k risk
    assert can_user_approve_record("Supervisor", "red", 25000.0) is True
    # Operator can approve GREEN tier
    assert can_user_approve_record("Operator", "green", 5000.0) is True


def test_soc2_worm_audit_log_exporter():
    logs = ["2026-07-21 12:00:00 INFO  test_event id=1"]
    json_export = export_soc2_audit_logs_json(logs)
    assert "SOC2_WORM_V1" in json_export
    assert "test_event" in json_export


def test_rlhf_confidence_calibration():
    desk = Desk()
    rec = process_message("STATUS: CNTR HELD PORT OF SAVANNAH", "edi", desk, SETTINGS)

    # Ingest 3 approval feedback events
    record_feedback(desk, rec.id, "approved")
    record_feedback(desk, rec.id, "approved")
    record_feedback(desk, rec.id, "approved")

    calibration_delta = calculate_rlhf_confidence_calibration("PORT_DELAY", desk)
    assert calibration_delta > 0.0
