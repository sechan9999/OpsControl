import json
import os
from dataclasses import replace
from pathlib import Path

import streamlit as st

from features.approval import approve_and_send, dismiss_exception, send_to_review, verify_pin
from features.booking import execute_alternative_carrier_booking
from features.email import get_default_sender
from features.ingest import ingest_batch, ingest_message, parse_feed_drop_content
from features.rbac import ROLES, can_user_approve_record, export_soc2_audit_logs_json, get_role_permissions
from opscontrol.config import Settings, settings_from_env
from opscontrol.graph_agent import SAMPLE_QUERIES, query_fabric_iq_agent
from opscontrol.store import Desk
from opscontrol.telemetry import get_port_telemetry, get_vessel_telemetry
from opscontrol.tools import alternative_carriers

st.set_page_config(page_title="OpsControl - AI Exception Desk", page_icon="🚢", layout="wide")

SEED_PATH = Path(__file__).parent / "data" / "savannah_storm.jsonl"
STATE_PATH = Path(os.getenv("OPSCONTROL_STATE_PATH", Path(__file__).parent / ".opscontrol_state.json"))
TIER_BADGE = {"red": "🔴 RED", "orange": "🟠 ORANGE", "green": "🟢 GREEN"}
STATUS_LABEL = {
    "ready_for_approval": "ready for approval",
    "needs_human_review": "needs human review",
    "triaged": "triaged", "investigating": "investigating", "drafting": "drafting",
    "sent": "sent", "dismissed": "dismissed",
}

SAMPLE_MESSAGES = {
    "Port delay (EDI)": "STATUS: CNTR MSKU9911223 SHPMT OPS-40077-B HELD PORT OF SAVANNAH REASON WX EST DELAY 18HRS",
    "Customs hold (email)": "Hi team, customs flagged shipment OPS-40078-C for documentation exam at Long Beach. Broker says 2-3 days. Consignee expects delivery Friday.",
    "Reefer alarm (SMS)": "reefer alarm OPS-40079-A temp -11C setpoint -18C tech dispatched",
    "Geopolitical strike (email)": "ALERT: Port closure and dockworker strike at Port of Savannah affecting shipment OPS-40021-A. Sanctions and port closure in effect for 5 days.",
    "Cyber attack outage (EDI)": "SYSTEM OUTAGE: Ransomware cyber attack hit carrier freight TMS. Terminal gate operations suspended for OPS-40026-C.",
    "No reference (email)": "A container is held at customs, no booking reference available yet, broker investigating documentation exam status.",
    "Malformed feed": "@@@#ERR 0x11 FEED RESYNC ]]]]] NO PAYLOAD {{{{",
}

SAMPLE_CHANNELS = {
    "Port delay (EDI)": "edi",
    "Customs hold (email)": "email",
    "Reefer alarm (SMS)": "sms",
    "Geopolitical strike (email)": "email",
    "Cyber attack outage (EDI)": "edi",
    "No reference (email)": "email",
    "Malformed feed": "edi",
}


def get_desk() -> Desk:
    if "desk" not in st.session_state:
        load_snapshot = getattr(Desk, "load", None)
        st.session_state.desk = load_snapshot(STATE_PATH) if callable(load_snapshot) else Desk()
        st.session_state.replayed = bool(st.session_state.desk.exceptions)
    return st.session_state.desk


def load_seed() -> list[dict]:
    return [json.loads(line) for line in SEED_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]


def persist_and_rerun() -> None:
    save_snapshot = getattr(desk, "save", None)
    if callable(save_snapshot):
        save_snapshot(STATE_PATH)
    st.rerun()


def generate_ontology_mermaid(triage, assessment) -> str:
    ref = triage.shipment_ref or "UNIDENTIFIED"
    exc_type = triage.exception_type
    sev = getattr(triage, "severity_label", "Medium")
    loc = triage.location or "Network Node"
    lines = ["graph TD"]
    lines.append(f'    E["⚡ Disruption: {exc_type}"] -->|affects| L["📍 Location: {loc}"]')
    lines.append(f'    L -->|supplies| S["📦 Shipment: {ref}"]')
    if assessment:
        at_risk = f"${assessment.affected_value:,.0f}" if assessment.affected_value else "$0"
        lines.append(f'    S -->|triggers| R["📊 Risk: {at_risk}"]')
        if assessment.mitigation_actions:
            for i, act in enumerate(assessment.mitigation_actions[:2]):
                lines.append(f'    R -->|recommends| A{i}["🛡️ Action: {act.action_type}"]')
    return "```mermaid\n" + "\n".join(lines) + "\n```"


def generate_network_cascade_mermaid(records, type_filter="All", sev_filter="All") -> str:
    filtered = []
    for r in records:
        t = r.triage
        sev_label = getattr(t, "severity_label", "Medium")
        if type_filter != "All" and t.exception_type != type_filter:
            continue
        if sev_filter != "All" and sev_label != sev_filter:
            continue
        filtered.append(r)

    if not filtered:
        return "```mermaid\ngraph LR\n    Empty['No active disruption cascades match filter']\n```"

    lines = ["graph LR"]
    for i, r in enumerate(filtered[:8]):
        t = r.triage
        a = r.assessment
        ref = t.shipment_ref or f"NO-REF-{r.id}"
        exc = t.exception_type
        loc = t.location or "Network Hub"
        risk_str = f"${a.affected_value:,.0f}" if (a and a.affected_value) else "$0"
        act_str = a.mitigation_actions[0].action_type if (a and a.mitigation_actions) else "MONITOR"

        d_id = f"D{i}"
        l_id = f"L{i}"
        s_id = f"S{i}"
        r_id = f"R{i}"
        a_id = f"A{i}"

        lines.append(f'    {d_id}["⚡ {exc}"] -->|affects| {l_id}["📍 {loc}"]')
        lines.append(f'    {l_id} -->|supplies| {s_id}["📦 {ref}"]')
        lines.append(f'    {s_id} -->|triggers| {r_id}["💰 {risk_str}"]')
        lines.append(f'    {r_id} -->|recommends| {a_id}["🛡️ {act_str}"]')

    return "```mermaid\n" + "\n".join(lines) + "\n```"


base_settings = settings_from_env()
desk = get_desk()

# ---------------------------------------------------------------------------
# Sidebar Layout
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Operator")
    operator_name = st.text_input("Name", placeholder="e.g. J. Park", key="operator-name")
    user_role = st.selectbox("Role (RBAC)", ROLES, index=0, help="Supervisor role required to approve RED tier exceptions >= $10k risk.", key="rbac-role")
    pin = st.text_input("Approval PIN", type="password", help="Enter name + PIN to enable Approve & send (demo PIN: 2468).", key="approval-pin")
    pin_valid = verify_pin(pin)
    operator_valid = bool(operator_name.strip())
    can_approve_base = pin_valid and operator_valid
    st.caption("Enter name + PIN to enable Approve & send (demo PIN: 2468).")

    st.header("Desk settings")
    threshold = st.slider(
        "Confidence threshold for auto-queue", 0.50, 0.90, 0.70, 0.05,
        help="Drafts at or above this confidence go to the approval inbox; below it, a human reviews first.",
    )

    if desk.exceptions:
        _preview_ready = sum(
            1 for r in desk.exceptions.values()
            if r.assessment and r.assessment.confidence >= (threshold + desk.adaptive_thresholds.get(r.triage.exception_type, 0.0))
            and r.status not in ("sent", "dismissed")
        )
        _preview_review = sum(
            1 for r in desk.exceptions.values()
            if r.assessment and r.assessment.confidence < (threshold + desk.adaptive_thresholds.get(r.triage.exception_type, 0.0))
            and r.status not in ("sent", "dismissed")
        )
        st.caption(
            f"At this threshold: **{_preview_ready}** → inbox &nbsp;|&nbsp; **{_preview_review}** → human review"
        )

    with st.expander("Adaptive thresholds (Feedback loop)"):
        if desk.adaptive_thresholds:
            for exc_type, offset in sorted(desk.adaptive_thresholds.items()):
                st.write(f"• `{exc_type}`: **{offset:+.2f}** (effective: {threshold + offset:.2f})")
        else:
            st.caption("No type threshold adjustments recorded yet. Feedback from human review automatically adjusts thresholds.")

    st.header("Ingest a carrier feed drop")
    uploaded_file = st.file_uploader(
        "EDI-style / JSONL batch (.txt, .jsonl)",
        type=["txt", "jsonl"],
        help="Upload EDI text feeds or JSONL batches.",
        key="feed-drop-file",
    )
    if st.button("Ingest feed drop", use_container_width=True, disabled=uploaded_file is None, key="ingest-drop-btn"):
        if uploaded_file:
            content_bytes = uploaded_file.getvalue()
            parsed_msgs = parse_feed_drop_content(content_bytes, uploaded_file.name)
            ingest_batch(parsed_msgs, desk, base_settings)
            persist_and_rerun()

    st.header("Inject a single message")
    sample_key = st.selectbox("Sample", list(SAMPLE_MESSAGES.keys()))
    custom = st.text_area("Or paste a raw carrier message", height=90, placeholder="STATUS: CNTR ... / any email or SMS text")

    settings = replace(base_settings, confidence_threshold=threshold)
    if st.button("Inject message", use_container_width=True):
        raw = custom.strip() or SAMPLE_MESSAGES[sample_key]
        channel = "email" if custom.strip() else SAMPLE_CHANNELS[sample_key]
        ingest_message(raw, channel, desk, settings)
        persist_and_rerun()

    with st.expander("Batch inject (one message per line)"):
        batch_channel = st.selectbox(
            "Channel for all messages",
            ["edi", "email", "sms", "webhook"],
            key="batch-channel",
        )
        batch_raw = st.text_area(
            "Paste messages (one per line)",
            height=120,
            placeholder="STATUS: CNTR ... HELD SAVANNAH\nreefer alarm OPS-...",
            key="batch-raw",
        )
        if st.button("Inject batch", use_container_width=True, key="batch-inject-btn"):
            lines = [l.strip() for l in batch_raw.splitlines() if l.strip()]
            if lines:
                batch_msgs = [{"raw": l, "channel": batch_channel} for l in lines]
                ingest_batch(batch_msgs, desk, settings)
                persist_and_rerun()
            else:
                st.warning("No messages to inject.")

    st.caption(
        "Demo mode uses a deterministic stub engine (zero tokens, reproducible). "
        "Set OPSCONTROL_DEMO_MODE=0 plus OPSCONTROL_USE_OPENAI=1 and OPENAI_API_KEY to enable live triage. "
        "[Repo](https://github.com/sechan9999/OpsControl)"
    )

# ---------------------------------------------------------------------------
# Main App Header & Metrics
# ---------------------------------------------------------------------------

st.title("OpsControl")
st.caption(
    "**An AI exception desk for freight ops.** Raw carrier messages are triaged, "
    "investigated with a bounded agent, prioritized, and drafted for one-click approval."
)

b1, b2, b3 = st.columns([2, 2, 1])
if b1.button("Replay the Savannah storm (32 messages)", type="primary", use_container_width=True):
    ingest_batch(load_seed(), desk, settings)
    st.session_state.replayed = True
    persist_and_rerun()
if b2.button("Replay again (all duplicates)", use_container_width=True,
             help="Re-sends the same 32 messages: idempotency drops every one.",
             disabled=not st.session_state.get("replayed")):
    ingest_batch(load_seed(), desk, settings)
    persist_and_rerun()
if b3.button("Reset desk", use_container_width=True):
    if STATE_PATH.exists():
        STATE_PATH.unlink()
    st.session_state.clear()
    st.rerun()

metrics = desk.metrics()
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Ingested", metrics["ingested"])
c2.metric("Duplicates dropped", metrics["duplicates"])
c3.metric("Ready for approval", metrics["ready"])
c4.metric("Needs human review", metrics["review"])
c5.metric("Sent", metrics["sent"])
c6.metric("Value at risk", f"${metrics['value_at_risk']:,.0f}")

if st.session_state.get("replayed"):
    reds = [record for record in desk.sorted_open() if record.tier == "red"]
    if reds:
        top = reds[0]
        st.error(
            f"**{metrics['ingested']} messages triaged.** Highest risk: "
            f"**{top.triage.shipment_ref or 'unidentified'}** - "
            f"{top.assessment.impact_summary if top.assessment else top.triage.summary}. "
            "Customer response is drafted below."
        )

open_records = desk.sorted_open()
review_records = desk.by_status("needs_human_review")
inbox_records = [record for record in open_records if record.status != "needs_human_review"]

tab_inbox, tab_ontology, tab_agent, tab_map, tab_review, tab_log = st.tabs([
    f"Inbox ({len(inbox_records)})",
    "온톨로지 대시보드 (Ontology Dashboard)",
    "Fabric IQ AI Agent",
    f"Disruption map ({len(open_records)})",
    f"Human review ({len(review_records)})",
    "Activity log",
])


def render_exception(record, namespace: str) -> None:
    triage, assessment, draft = record.triage, record.assessment, record.draft
    arrived = record.created_at[11:19] if record.created_at else ""  # HH:MM:SS
    sev_label = getattr(triage, "severity_label", "Medium")
    title = (
        f"{TIER_BADGE[record.tier]} | {triage.shipment_ref or 'NO-REF'} | "
        f"{triage.exception_type} | sev {triage.severity} ({sev_label}) | {STATUS_LABEL[record.status]}"
        + (f" | arrived {arrived}" if arrived else "")
    )
    with st.expander(title, expanded=False):
        left, right = st.columns([3, 2])
        with left:
            st.markdown(f"**Summary:** {triage.summary}")
            st.markdown(f"**Customer impact:** {triage.customer_impact}")
            est_duration = getattr(triage, "estimated_duration_days", None)
            if est_duration:
                st.markdown(f"**Est. disruption duration:** {est_duration} days")
            if assessment:
                st.markdown(f"**Assessment:** {assessment.impact_summary}")
                conf_label = getattr(assessment, "confidence_label", "Medium")
                time_days = getattr(assessment, "time_to_impact_days", None)
                time_impact = (
                    f"⏱ {time_days:.1f}d to window"
                    if time_days is not None and time_days > 0
                    else ("⚠ window MISSED" if assessment.window_missed else "window holds")
                )
                st.markdown(
                    f"**Confidence:** {conf_label} ({assessment.confidence:.2f}) | **Rounds:** {assessment.rounds_used}/5 | "
                    f"**Timeline:** {time_impact} | "
                    f"**At risk:** ${assessment.affected_value:,.0f}"
                )
                mitigation_actions = getattr(assessment, "mitigation_actions", [])
                if mitigation_actions:
                    st.markdown("**Structured Mitigation Cascade (Ontology Grounded):**")
                    for act in mitigation_actions:
                        cost_str = f" • Est cost: ${act.estimated_cost_usd:,.0f}" if act.estimated_cost_usd else ""
                        saved_str = f" • Save {act.lead_time_saved_days}d" if act.lead_time_saved_days else ""
                        status_chip = f" [`{act.status}`]" if act.status != "proposed" else ""
                        st.markdown(f"• `{act.action_type}`{status_chip}: {act.description}{cost_str}{saved_str}")

            # One-Click Alternative Carrier Booking Tender UI
            has_alt_action = any(a.action_type == "ACTIVATE_ALTERNATIVE_CARRIER" for a in (assessment.mitigation_actions if assessment else []))
            if has_alt_action:
                lane_val = "SAV->RDU" if (triage.shipment_ref == "OPS-40045-A") else ("SAV->ATL" if "sav" in (triage.location or "").lower() else "MEM->ORD")
                alts = alternative_carriers(lane_val)
                with st.expander("🚚 One-Click Alternative Carrier Tender Booking", expanded=False):
                    alt_names = [f"{a.name} ({a.capacity_available}, +{a.price_premium_pct:.1f}% cost, {a.qualification_status})" for a in alts]
                    selected_idx = st.selectbox("Select Pre-Qualified Backup Carrier", range(len(alts)), format_func=lambda i: alt_names[i], key=f"{namespace}-alt-sel-{record.id}")
                    if st.button("Execute Carrier Tender Booking", key=f"{namespace}-tender-btn-{record.id}"):
                        receipt = execute_alternative_carrier_booking(desk, record.id, alts[selected_idx], operator_name=operator_name.strip() or "Operator")
                        st.success(f"Tender #{receipt.booking_id} confirmed with {receipt.carrier_name} for ${receipt.estimated_cost_usd:,.0f} USD.")
                        persist_and_rerun()

            if draft:
                st.text_input("Email subject", draft.email_subject, key=f"{namespace}-subj-{record.id}")
                st.text_area("Customer email draft (editable)", draft.email_body,
                             height=200, key=f"{namespace}-body-{record.id}")
                st.markdown("**Internal action plan**")
                st.markdown(draft.action_plan)

        with right:
            st.markdown("**Raw message**")
            st.code(record.raw, language="text", wrap_lines=True)

            # Live AIS Vessel & Port Terminal Telemetry
            vessel_tel = get_vessel_telemetry(triage.shipment_ref)
            port_tel = get_port_telemetry(triage.location)
            if vessel_tel or port_tel:
                with st.expander("📡 Live AIS Vessel & Port Telemetry", expanded=True):
                    if vessel_tel:
                        st.markdown(f"**Vessel:** {vessel_tel.vessel_name} ({vessel_tel.flag}) | **Speed:** {vessel_tel.speed_knots} kts | **Status:** {vessel_tel.status}")
                        st.markdown(f"**ETA (UTC):** `{vessel_tel.eta_utc}` | **Anchorage Dwell:** {vessel_tel.anchorage_dwell_hours}h")
                    if port_tel:
                        st.markdown(f"**Port Node:** {port_tel.port_name} (`{port_tel.code}`) | **Congestion:** {port_tel.congestion_index*100:.0f}%")
                        st.markdown(f"**Status:** `{port_tel.terminal_status}` | **Weather:** {port_tel.weather_condition} ({port_tel.wind_knots} kts)")

            st.markdown("**Ontology Cascade Graph**")
            st.markdown(generate_ontology_mermaid(triage, assessment))
            if assessment and assessment.trace:
                st.markdown("**Agent trace**")
                st.json(assessment.trace, expanded=False)

        if record.status in ("ready_for_approval", "needs_human_review"):
            affected_val = assessment.affected_value if assessment else 0.0
            rbac_can_approve = can_user_approve_record(user_role, record.tier, affected_val)
            allow_approve = can_approve_base and rbac_can_approve

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                btn_approve = st.button(
                    "Approve & send",
                    key=f"{namespace}-approve-{record.id}",
                    use_container_width=True,
                    disabled=not allow_approve,
                    help="Requires Supervisor role for RED tier >= $10k risk" if (can_approve_base and not rbac_can_approve) else ("Requires Name + PIN (2468)" if not can_approve_base else "Approve and deliver customer email"),
                )
                if btn_approve:
                    subject = st.session_state.get(f"{namespace}-subj-{record.id}", draft.email_subject if draft else None)
                    body = st.session_state.get(f"{namespace}-body-{record.id}", draft.email_body if draft else None)
                    approve_and_send(desk, record.id, subject=subject, body=body, operator_name=operator_name.strip() or "Operator", pin=pin)
                    persist_and_rerun()
            with col_b:
                if st.button("Send to review", key=f"{namespace}-review-{record.id}", use_container_width=True):
                    send_to_review(desk, record.id, note="operator_escalated", by=operator_name.strip() or "operator")
                    persist_and_rerun()
            with col_c:
                if st.button("Dismiss", key=f"{namespace}-dismiss-{record.id}", use_container_width=True):
                    dismiss_exception(desk, record.id, note="operator_dismissed", by=operator_name.strip() or "operator")
                    persist_and_rerun()


with tab_inbox:
    if not inbox_records:
        st.info("Inbox is clear. Replay the Savannah storm or inject a message from the sidebar.")
    for r in inbox_records:
        render_exception(r, namespace="inbox")

with tab_ontology:
    st.subheader("🌐 Microsoft Supply Chain Ontology Cascade Dashboard")
    st.caption("Visualizing the 5-tier disruption cascade: **Disruption Event (파괴 사건) → Location/Port (위치) → Cargo/Shipment (화물) → Risk Exposure (손실 위험액) → Mitigation Action (대안 조치)**")

    f1, f2 = st.columns(2)
    all_types = sorted(list(set(r.triage.exception_type for r in open_records))) if open_records else []
    selected_type = f1.selectbox("Filter by Disruption Type", ["All"] + all_types, key="ont-type-filter")
    selected_sev = f2.selectbox("Filter by Severity Level", ["All", "Critical", "High", "Medium", "Low"], key="ont-sev-filter")

    filtered_open = []
    for r in open_records:
        t = r.triage
        sev_label = getattr(t, "severity_label", "Medium")
        if selected_type != "All" and t.exception_type != selected_type:
            continue
        if selected_sev != "All" and sev_label != selected_sev:
            continue
        filtered_open.append(r)

    tot_risk = sum((r.assessment.affected_value if r.assessment else 0.0) for r in filtered_open)
    avg_impact_days = [r.assessment.time_to_impact_days for r in filtered_open if r.assessment and r.assessment.time_to_impact_days is not None]
    avg_impact_str = f"{sum(avg_impact_days)/len(avg_impact_days):.1f}d" if avg_impact_days else "N/A"
    in_prog_tenders = sum(1 for r in filtered_open if r.assessment and any(a.status == "in_progress" for a in (r.assessment.mitigation_actions or [])))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Active Disruption Cascades", len(filtered_open))
    m2.metric("Total Risk Exposure", f"${tot_risk:,.0f} USD")
    m3.metric("Avg Time to Impact", avg_impact_str)
    m4.metric("Active Backup Tenders", in_prog_tenders)

    st.markdown("### 📊 Network-Wide Visual Cascade Graph (Mermaid Flowchart)")
    st.markdown(generate_network_cascade_mermaid(open_records, selected_type, selected_sev))

    st.markdown("### 📋 Disruption & Mitigation Cascade Matrix")
    if filtered_open:
        matrix_rows = []
        for r in filtered_open:
            t = r.triage
            a = r.assessment
            acts = a.mitigation_actions if a else []
            primary_act = acts[0].description if acts else (a.recommended_action if a else "Manual Review")
            act_type = acts[0].action_type if acts else "MONITOR"
            act_status = acts[0].status if acts else "proposed"
            time_str = f"{a.time_to_impact_days:.1f}d" if (a and a.time_to_impact_days is not None) else ("MISSED" if (a and a.window_missed) else "Holding")

            matrix_rows.append({
                "ID": r.id,
                "Disruption Event": f"⚡ {t.exception_type}",
                "Severity": f"{t.severity} ({getattr(t, 'severity_label', 'Medium')})",
                "Location": t.location or "Network Hub",
                "Shipment Ref": t.shipment_ref or "UNIDENTIFIED",
                "Risk Exposure ($)": f"${a.affected_value:,.0f}" if a else "$0",
                "Timeline": time_str,
                "Primary Mitigation Action": f"[{act_type}] {primary_act}",
                "Action Status": act_status,
            })
        st.dataframe(matrix_rows, use_container_width=True)
    else:
        st.info("No active disruption cascades match the selected filter criteria.")

with tab_agent:
    st.subheader("🌐 Microsoft Fabric IQ AI Graph Agent")
    st.markdown("Ask natural language questions grounded in the supply chain disruption ontology graph.")

    q_choice = st.selectbox("Sample Queries", SAMPLE_QUERIES, key="graph-q-choice")
    user_q = st.text_input("Or type your supply chain question", value=q_choice, key="graph-q-input")

    if st.button("Query Fabric IQ Agent", type="primary", key="query-agent-btn"):
        res = query_fabric_iq_agent(user_q, desk)
        st.success(f"**Agent Response:** {res.summary_answer}")

        ca, cb = st.columns([1, 1])
        with ca:
            st.markdown("**Cypher Graph Traversal Query**")
            st.code(res.cypher_query, language="cypher")
            st.metric("Matched Graph Nodes", res.affected_nodes)
            st.metric("Total Revenue Exposure", f"${res.revenue_at_risk_usd:,.0f} USD")
        with cb:
            st.markdown("**Grounding Graph Subgraph**")
            st.markdown(res.mermaid_subgraph)
            if res.matched_records:
                st.markdown("**Matched Network Entities**")
                st.json(res.matched_records, expanded=False)

with tab_map:
    if not open_records:
        st.info("No active disruptions on network.")
    else:
        st.subheader("Active Disruption Overview")
        rows = []
        for r in open_records:
            t = r.triage
            a = r.assessment
            rows.append({
                "ID": r.id,
                "Ref": t.shipment_ref or "UNIDENTIFIED",
                "Tier": r.tier.upper(),
                "Disruption Type": t.exception_type,
                "Severity": f"{t.severity} ({getattr(t, 'severity_label', 'Medium')})",
                "Location": t.location or "Global",
                "At Risk": f"${a.affected_value:,.0f}" if a else "$0",
                "Status": r.status,
            })
        st.dataframe(rows, use_container_width=True)

with tab_review:
    if not review_records:
        st.info("No exceptions require human review.")
    for r in review_records:
        render_exception(r, namespace="review")

with tab_log:
    st.subheader("Event & Audit Log")
    col_log_h, col_log_dl = st.columns([3, 1])
    with col_log_h:
        st.markdown(f"**Total Audit Events:** {len(desk.logs)}")
    with col_log_dl:
        worm_json = export_soc2_audit_logs_json(desk.logs)
        st.download_button(
            "Download SOC2 WORM Log (JSON)",
            data=worm_json,
            file_name="soc2_audit_trail.json",
            mime="application/json",
            use_container_width=True,
        )
    if desk.logs:
        st.code("\n".join(desk.logs), language="text")
    else:
        st.info("No audit logs yet.")

default_sender = get_default_sender()
smtp_status = "configured (live SMTP)" if getattr(default_sender, "mode", "") == "smtp" else "not configured (using mock)"
st.caption(f"Channels: feed drop + manual inject | Approval: operator + PIN ({user_role}) | Delivery: SMTP {smtp_status}")
