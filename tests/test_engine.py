import json
from pathlib import Path

from opscontrol.config import Settings, settings_from_env
from opscontrol.pipeline import process_message
from opscontrol.store import Desk
from opscontrol.tiering import tier
from opscontrol.triage import stub_triage

SETTINGS = Settings()
SEED = Path(__file__).parent.parent / "data" / "savannah_storm.jsonl"

PHARMA_MSG = (
    "Escalation: OPS-40045-A is temperature-sensitive pharma with a hard delivery "
    "window Thursday 08:00-12:00. Current Savannah hold puts arrival at Thursday "
    "15:40. Client contract has a $25k OTIF penalty clause. Need options today please."
)


def load_seed():
    return [json.loads(l) for l in SEED.read_text(encoding="utf-8").splitlines() if l.strip()]


# ---- triage --------------------------------------------------------------

def test_triage_parses_edi_port_delay():
    t = stub_triage(
        "STATUS: CNTR MSKU7401229 SHPMT OPS-40021-A HELD PORT OF SAVANNAH "
        "REASON WX SEVERE RAIN EST DELAY 14HRS NEXT UPDATE 0600", "edi")
    assert t.shipment_ref == "OPS-40021-A"
    assert t.exception_type == "PORT_DELAY"
    assert t.location == "Port of Savannah"
    assert t.delay_hours == 14


def test_triage_malformed_is_unknown():
    t = stub_triage("@@@#ERR 0x004452 FEED RESYNC ]]]]] NO PAYLOAD {{{{", "edi")
    assert t.exception_type == "UNKNOWN"
    assert t.shipment_ref is None


def test_triage_pharma_escalation_is_severity_5():
    t = stub_triage(PHARMA_MSG, "email")
    assert t.shipment_ref == "OPS-40045-A"
    assert t.severity == 5


# ---- tiering --------------------------------------------------------------

def test_tier_rules():
    assert tier(5, False, 0) == "red"
    assert tier(2, True, 25000) == "red"
    assert tier(3, False, 0) == "orange"
    assert tier(2, True, 500) == "orange"
    assert tier(1, False, 0) == "green"


# ---- pipeline -------------------------------------------------------------

def test_duplicate_suppressed():
    desk = Desk()
    raw = "STATUS: SHPMT OPS-40099-Z HELD SAVANNAH DELAY 5HRS"
    first = process_message(raw, "edi", desk, SETTINGS)
    second = process_message(raw, "edi", desk, SETTINGS)
    assert first is not None and second is None
    assert desk.counters["duplicates"] == 1
    assert len(desk.exceptions) == 1


def test_malformed_routes_to_review_without_agent():
    desk = Desk()
    rec = process_message("@@@#ERR 0x004452 FEED RESYNC ]]]]] NO PAYLOAD {{{{", "edi", desk, SETTINGS)
    assert rec.status == "needs_human_review"
    assert rec.assessment is None  # agent never ran


def test_pharma_full_pipeline():
    desk = Desk()
    rec = process_message(PHARMA_MSG, "email", desk, SETTINGS)
    a = rec.assessment
    assert a is not None
    assert a.window_missed is True
    assert a.affected_value == 25000
    assert rec.tier == "red"
    assert rec.status == "ready_for_approval"
    assert rec.draft is not None and "OPS-40045-A" in rec.draft.email_subject
    assert 1 <= a.rounds_used <= SETTINGS.max_rounds
    assert len(a.trace) >= 3  # lookup + conditions + eta


def test_no_ref_message_bounded_and_low_confidence():
    desk = Desk()
    rec = process_message(
        "Team, a container is held at customs, no booking reference available yet, "
        "broker investigating documentation exam status.", "email", desk, SETTINGS)
    a = rec.assessment
    assert a.rounds_used <= SETTINGS.max_rounds
    assert rec.status == "needs_human_review"  # low confidence without shipment identity
    assert any("error" in step["result"] for step in a.trace)


def test_terminal_states_are_protected():
    desk = Desk()
    rec = process_message(PHARMA_MSG, "email", desk, SETTINGS)
    desk.set_status(rec.id, "sent")
    try:
        desk.set_status(rec.id, "dismissed")
        raise AssertionError("terminal transition was allowed")
    except ValueError:
        pass


# ---- full seed replay -----------------------------------------------------

def test_seed_replay_end_to_end():
    desk = Desk()
    for m in load_seed():
        process_message(m["raw"], m["channel"], desk, SETTINGS)

    metrics = desk.metrics()
    assert metrics["ingested"] == 29           # 32 lines - 3 duplicates
    assert metrics["duplicates"] == 3
    assert metrics["review"] >= 2              # malformed + at least one low-confidence
    assert metrics["ready"] >= 10

    # every investigation stayed bounded
    for r in desk.exceptions.values():
        if r.assessment:
            assert r.assessment.rounds_used <= SETTINGS.max_rounds

    # the pharma escalation is the top of the queue
    top = desk.sorted_open()[0]
    assert top.triage.shipment_ref == "OPS-40045-A"
    assert top.tier == "red"

# ---- demo resilience ------------------------------------------------------

def test_desk_snapshot_round_trips(tmp_path):
    desk = Desk()
    record = process_message(PHARMA_MSG, "email", desk, SETTINGS)
    desk.set_status(record.id, "sent")
    snapshot = tmp_path / "desk.json"
    desk.save(snapshot)

    # Verify schema_version is written (#13)
    raw = json.loads(snapshot.read_text(encoding="utf-8"))
    assert raw["schema_version"] == 1

    restored = Desk.load(snapshot)
    restored_record = restored.exceptions[record.id]
    assert restored.metrics() == desk.metrics()
    assert restored_record.status == "sent"
    assert restored_record.triage.shipment_ref == "OPS-40045-A"
    assert restored_record.assessment is not None
    assert restored_record.draft is not None


def test_demo_mode_disables_live_openai(monkeypatch):
    monkeypatch.setenv("OPSCONTROL_USE_OPENAI", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    settings = settings_from_env()
    assert settings.demo_mode is True
    assert settings.use_openai is False


def test_live_triage_requires_explicit_demo_opt_out(monkeypatch):
    monkeypatch.setenv("OPSCONTROL_DEMO_MODE", "0")
    monkeypatch.setenv("OPSCONTROL_USE_OPENAI", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert settings_from_env().use_openai is True