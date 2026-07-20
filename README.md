# OpsControl

Freight Desk OpsControl is a human-in-the-loop operations exception desk for freight teams. It converts a surge of carrier updates into a prioritized queue, impact assessments, customer-ready drafts, and a focused review list.
https://devpost.com/software/freightdesk

## Live demo

[opscontrol.streamlit.app](https://opscontrol.streamlit.app/)

The deployed demo uses deterministic scenario data. No account, API key, or credentials are required for judges.

### Judge test path

1. Click **Reset desk**.
2. Click **Replay the Savannah storm (32 messages)**.
3. Open the top red item, `OPS-40045-A`, and inspect the assessment, five-round trace, draft, and action plan.
4. Click **Approve & send** to exercise the required human approval step.
5. Open **Human review** to inspect ambiguous and malformed input safely escalated to an operator.
6. Click **Replay again (all duplicates)** to verify that repeated deliveries do not create new work.

## What it demonstrates

- Normalized-message idempotency: three duplicate deliveries are identified during the 32-message replay.
- Bounded investigation: each assessment uses at most five tool rounds.
- Prioritized risk: the pharma escalation `OPS-40045-A` has a missed window and $25,000 at risk.
- Human control: customer communication is editable and cannot be marked sent without approval.
- Safe failure handling: malformed and low-confidence updates appear in Human review instead of being silently guessed or discarded.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Run the regression suite:

```bash
python -m pytest
```

## OpenAI and Codex

OpsControl was built with Codex to scaffold the workflow, implement guardrails, and create regression coverage. The default demo uses deterministic triage so judges receive the same result without credentials.

An optional GPT-5.6 structured-triage path is included for local use. Keep secrets out of Git: set `OPSCONTROL_DEMO_MODE=0`, `OPSCONTROL_USE_OPENAI=1`, and `OPENAI_API_KEY` in an untracked `.env` file or in Streamlit secrets. The application falls back to deterministic triage if a live request fails.

## Project structure

- `streamlit_app.py` - operator control surface
- `opscontrol/` - triage, investigation, composition, storage, and workflow engine
- `data/savannah_storm.jsonl` - deterministic 32-message scenario
- `tests/` - replay and guardrail tests
- `docs/PRD.md` - product requirements
- `docs/seed-data-spec.md` - scenario contract
- `docs/submission-checklist.md` - final hackathon submission checklist

## Roadmap

The next step is to connect real carrier channels: EDI 214/315 feeds, email ingestion, and webhook events. From there, OpsControl can add authenticated approval, real email delivery, customer-specific communication preferences, and feedback from review outcomes to improve routing over time.
