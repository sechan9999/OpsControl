import json
from opscontrol.graph_agent import query_fabric_iq_agent
from opscontrol.models import AlternativeCarrier
from opscontrol.store import Desk
from features.booking import calculate_tender_tradeoff
from features.rbac import export_soc2_audit_logs_json, verify_soc2_audit_chain


def test_tender_financial_tradeoff_calculation():
    desk = Desk()
    carrier = AlternativeCarrier(
        name="ColdExpress",
        lane="SAV->RDU",
        price_premium_pct=8.0,
        capacity_available="12 loads/wk",
        qualification_status="approved",
    )
    # Mock exception record with affected value
    desk.log("info", "test_event", payload="sample")
    tradeoff = calculate_tender_tradeoff(None, carrier)
    assert tradeoff.backup_carrier_cost_usd > 0
    assert tradeoff.net_benefit_usd > 0
    assert tradeoff.roi_percentage > 0


def test_soc2_audit_log_hash_chain_verification():
    logs = [
        "2026-07-21T18:00:00Z [info] system_started",
        "2026-07-21T18:05:00Z [info] message_ingested id=1 ref=OPS-40045-A",
        "2026-07-21T18:10:00Z [info] approval_granted id=1 by=J. Park",
    ]
    export_json = export_soc2_audit_logs_json(logs)
    parsed = json.loads(export_json)
    
    assert parsed["crypto_schema"] == "SHA-256_HASH_CHAIN"
    assert len(parsed["hash_chain"]) == 3
    assert verify_soc2_audit_chain(export_json) is True

    # Test tampering detection
    tampered_data = json.loads(export_json)
    tampered_data["logs"][1] = "2026-07-21T18:05:00Z [info] TAMPERED_EVENT"
    tampered_json = json.dumps(tampered_data)
    assert verify_soc2_audit_chain(tampered_json) is False


def test_fabric_iq_scenario_simulation_query():
    desk = Desk()
    res = query_fabric_iq_agent("Compare rerouting via Charleston (USCHS) vs waiting at Savannah", desk)
    assert "Charleston" in res.summary_answer
    assert "SIMULATE PATH" in res.cypher_query
    assert len(res.matched_records) >= 2
