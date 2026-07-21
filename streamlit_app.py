import json
import os
from dataclasses import replace
from pathlib import Path

import streamlit as st

from features.approval import approve_and_send, dismiss_exception, send_to_review
from features.ingest import ingest_batch, ingest_message
from opscontrol.config import Settings, settings_from_env
from opscontrol.store import Desk

st.set_page_config(page_title="OpsControl - AI Exception Desk", page_icon="FD", layout="wide")

SEED_PATH = Path(__file__).parent / "data" / "savannah_storm.jsonl"
STATE_PATH = Path(os.getenv("OPSCONTROL_STATE_PATH", Path(__file__).parent / ".opscontrol_state.json"))
TIER_BADGE = {"red": "RED", "orange": "ORANGE", "green": "GREEN"}
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
    "No reference (email)": "A container is held at customs, no booking reference available yet, broker investigating documentation exam status.",
    "Malformed feed": "@@@#ERR 0x11 FEED RESYNC ]]]]] NO PAYLOAD {{{{",
}

SAMPLE_CHANNELS = {
    "Port delay (EDI)": "edi",
    "Customs hold (email)": "email",
    "Reefer alarm (SMS)": "sms",
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



base_settings = settings_from_env()

desk = get_desk()

with st.sidebar:
    st.header("Desk settings")
    threshold = st.slider(
        "Confidence threshold for auto-queue", 0.50, 0.90, 0.70, 0.05,
        help="Drafts at or above this confidence go to the approval inbox; below it, a human reviews first.",
    )
    # Live preview — how many records move at this threshold (#5)
    if desk.exceptions:
        _preview_ready = sum(
            1 for r in desk.exceptions.values()
            if r.assessment and r.assessment.confidence >= threshold
            and r.status not in ("sent", "dismissed")
        )
        _preview_review = sum(
            1 for r in desk.exceptions.values()
            if r.assessment and r.assessment.confidence < threshold
            and r.status not in ("sent", "dismissed")
        )
        st.caption(
            f"At this threshold: **{_preview_ready}** → inbox &nbsp;|&nbsp; **{_preview_review}** → human review"
        )

    st.header("Inject a single message")
    sample_key = st.selectbox("Sample", list(SAMPLE_MESSAGES.keys()))
    custom = st.text_area("Or paste a raw carrier message", height=90, placeholder="STATUS: CNTR ... / any email or SMS text")

    settings = replace(base_settings, confidence_threshold=threshold)
    if st.button("Inject message", use_container_width=True):
        raw = custom.strip() or SAMPLE_MESSAGES[sample_key]
        channel = "email" if custom.strip() else SAMPLE_CHANNELS[sample_key]
        ingest_message(raw, channel, desk, settings)
        persist_and_rerun()

    # Batch inject UI (#4)
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
tab_inbox, tab_review, tab_log = st.tabs([
    f"Inbox ({len(inbox_records)})",
    f"Human review ({len(review_records)})",
    "Activity log",
])


def render_exception(record, namespace: str) -> None:
    triage, assessment, draft = record.triage, record.assessment, record.draft
    arrived = record.created_at[11:19] if record.created_at else ""  # HH:MM:SS
    title = (
        f"{TIER_BADGE[record.tier]} | {triage.shipment_ref or 'NO-REF'} | "
        f"{triage.exception_type} | sev {triage.severity} | {STATUS_LABEL[record.status]}"
        + (f" | arrived {arrived}" if arrived else "")
    )
    with st.expander(title, expanded=False):
        left, right = st.columns([3, 2])
        with left:
            st.markdown(f"**Summary:** {triage.summary}")
            st.markdown(f"**Customer impact:** {triage.customer_impact}")
            if assessment:
                st.markdown(f"**Assessment:** {assessment.impact_summary}")
                st.markdown(
                    f"**Confidence:** {assessment.confidence:.2f} | **Rounds:** {assessment.rounds_used}/5 | "
                    f"**Window missed:** {'yes' if assessment.window_missed else 'no'} | "
                    f"**At risk:** ${assessment.affected_value:,.0f}"
                )
            if draft:
                st.text_input("Email subject", draft.email_subject, key=f"{namespace}-subj-{record.id}")
                st.text_area("Customer email draft (editable)", draft.email_body,
                             height=200, key=f"{namespace}-body-{record.id}")
                st.markdown("**Internal action plan**")
                st.markdown(draft.action_plan)
        with right:
            st.markdown("**Raw message**")
            st.code(record.raw, language="text", wrap_lines=True)
            if assessment and assessment.trace:
                st.markdown("**Agent trace**")
                st.json(assessment.trace, expanded=False)

        if record.status in ("ready_for_approval", "needs_human_review"):
            col_a, col_b, col_c = st.columns(3)
            if col_a.button("Approve & send", key=f"{namespace}-approve-{record.id}", use_container_width=True):
                subject = (
                    st.session_state.get(
                        f"{namespace}-subj-{record.id}",
                        draft.email_subject,
                    )
                    if draft
                    else None
                )
                body = (
                    st.session_state.get(
                        f"{namespace}-body-{record.id}",
                        draft.email_body,
                    )
                    if draft
                    else None
                )
                approve_and_send(
                    desk,
                    record.id,
                    subject=subject,
                    body=body,
                )
                persist_and_rerun()
            if record.status == "ready_for_approval":
                if col_b.button("Send to review", key=f"{namespace}-review-{record.id}", use_container_width=True):
                    send_to_review(desk, record.id)
                    persist_and_rerun()
            if col_c.button("Dismiss", key=f"{namespace}-dismiss-{record.id}", use_container_width=True):
                dismiss_exception(desk, record.id)
                persist_and_rerun()


with tab_inbox:
    if not inbox_records:
        st.info("Inbox is clear. Replay the Savannah storm or inject a message from the sidebar.")
    for record in inbox_records:
        render_exception(record, namespace="inbox")

with tab_review:
    if not review_records:
        st.info("Nothing waiting on a human. The agent is confident about everything open.")
    else:
        st.warning("These need human judgment: unclassified feeds, unidentified shipments, or low confidence.")
        for record in review_records:
            render_exception(record, namespace="review")

with tab_log:
    if desk.logs:
        st.code("\n".join(desk.logs[:120]), language="text")
    else:
        st.info("No activity yet.")
