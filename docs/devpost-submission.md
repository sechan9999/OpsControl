# Devpost submission: OpsControl

## Project name

OpsControl

## Elevator pitch

OpsControl turns a flood of carrier updates into a prioritized operations queue, customer-ready drafts, and a focused human-review list.

## Project description

### The problem

A port disruption can generate dozens of EDI updates, emails, and driver messages in minutes. Each one creates a decision: identify the shipment, estimate customer impact, decide what matters now, and communicate the result. Duplicates and malformed feeds make an already overloaded workflow worse.

### The solution

OpsControl is a human-in-the-loop operations exception desk. It ingests carrier-style updates, classifies the exception, investigates the impact with a bounded evidence loop, prioritizes the queue, and prepares a customer draft plus an internal action plan.

High-confidence cases move to **Ready for approval**. Ambiguous, malformed, or low-confidence cases move to **Human review**. Operators can inspect the raw message and trace, edit the draft, and explicitly approve before a record is marked sent.

The Savannah storm replay contains 32 realistic messages: 29 unique records, three duplicate deliveries, malformed input, and a temperature-sensitive pharma shipment with a missed window and $25,000 at risk.

The implementation keeps external integrations separate from the core decision
engine. This allows the same guardrails, approval rules, and audit behavior to be
used with deterministic demo data or production carrier adapters.

### Guardrails

OpsControl treats reliability as a product feature:

- Idempotency prevents repeat carrier updates from creating duplicate work.
- Investigation is capped at five rounds and remains traceable.
- Low-confidence or malformed input routes safely to human review.
- The operator remains in control of any external communication.
- The demo scenario is deterministic and requires no credentials.

### How Codex and GPT-5.6 were used

Codex was used to develop the workflow, guardrails, replay fixture, persistence, and regression suite. The default demo uses deterministic triage so judges can replay the same outcome without an API key.

OpsControl also includes an opt-in GPT-5.6 structured-triage path for live carrier text. It is disabled in demo mode, requires explicit environment configuration, and falls back safely to deterministic triage if the live request fails.

### Built for extension

OpsControl separates the operational workflow into explicit feature boundaries:

- Validated EDI, email, SMS, and webhook ingestion
- Human-controlled approval and review actions
- A delivery adapter that is deterministic in the demo and replaceable in production
- Customer-specific communication profiles
- Structured feedback events for operator outcomes

The public demo intentionally performs no external delivery and requires no
credentials. Production adapters can connect these boundaries to authenticated
EDI 214/315 feeds, monitored inboxes, signed webhooks, transactional email
providers, tenant-level preferences, and persisted feedback analytics.

## Private judge access field

No credentials, account, or API key are required for the deterministic demo.

Target app URL: https://opscontrol.streamlit.app/

1. Click **Reset desk**.
2. Click **Replay the Savannah storm (32 messages)**.
3. Open `OPS-40045-A` in the Inbox to inspect its assessment, trace, draft, and action plan.
4. Approve the draft, then open **Human review** to see ambiguous cases safely escalated.
5. Click **Replay again (all duplicates)** to verify that duplicate deliveries do not create more work.

Repository: https://github.com/sechan9999/OpsControl