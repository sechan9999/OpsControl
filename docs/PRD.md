# OpsControl Product Requirements Document

## 1. Product summary

OpsControl is a human-in-the-loop operations exception desk. It converts incoming operational updates from EDI-style feeds, emails, SMS-like messages, and webhooks into a prioritized work queue. For each exception, OpsControl identifies the affected entity, estimates impact, gathers bounded supporting evidence, drafts a stakeholder response and internal action plan, then routes the case either to approval or human review.

The initial vertical is freight and logistics, but the domain model must remain general enough for other high-volume operational workflows.

## 2. Problem

Operations teams receive fragmented status updates during incidents. A single disruption creates repetitive, incomplete, contradictory, and duplicate messages. Staff must manually identify the affected shipment or job, decide severity, determine whether a deadline is threatened, communicate the status, and maintain an audit trail.

The result is a slow, unprioritized inbox. Important cases are easy to miss, and automatic action is unsafe when an update lacks sufficient context.

## 3. Goal and success criteria

### Goal

Give an operator a reliable control surface that makes the next best operational decision obvious while keeping the operator responsible for final outward-facing action.

### Success criteria for the MVP

- A replay of 32 scenario messages produces one stable, prioritized queue.
- Exact redeliveries do not create duplicate work or trigger repeat processing.
- Every accepted message ends in `ready_for_approval`, `needs_human_review`, `sent`, or `dismissed`.
- Investigation uses no more than five tool rounds per exception.
- Unknown, malformed, or low-confidence inputs reach human review without crashing the workflow.
- The top scenario item is a high-risk pharma shipment with a missed window and $25,000 at risk.
- The full replay and core guardrails are covered by automated tests.

## 4. Users

### Operations coordinator

Monitors incoming updates, reviews priority, edits drafted messages, approves customer communication, and escalates ambiguous cases.

### Operations manager

Needs a concise view of active risk, duplicate suppression, review backlog, and the evidence behind automation.

### Customer stakeholder

Receives a human-approved, accurate status update. This user does not interact with the MVP directly.

## 5. MVP scope

### In scope

- Raw message ingestion through a local API or UI injection point.
- Deterministic structured triage for the initial demo.
- Shipment or reference extraction, exception classification, severity, location, delay, and confidence.
- Bounded investigation via deterministic lookup tools.
- Impact assessment, prioritization, customer draft, and internal action plan.
- Approval inbox, human-review queue, activity log, and replay scenario.
- Persistent local state suitable for Streamlit reruns.
- Explicit demonstration mode that requires no credentials or external network calls.

### Out of scope

- Live carrier credentials and production EDI connectivity.
- Real email or SMS sending.
- Automatic approval or automatic customer delivery.
- Multi-tenant access control, SSO, billing, and configurable workflows.
- Learning from user feedback in the MVP.

## 6. Core workflow

```text
message received
  -> normalize and deduplicate
  -> triage into a structured exception
  -> investigate impact (maximum five rounds)
  -> compose customer draft and action plan
  -> ready_for_approval OR needs_human_review
  -> human approves and marks sent, or dismisses
```

### States

| State | Meaning | Allowed next states |
| --- | --- | --- |
| `received` | Raw update accepted | `triaged`, `needs_human_review` |
| `triaged` | Structured facts extracted | `investigating`, `needs_human_review` |
| `investigating` | Bounded evidence lookup in progress | `drafting`, `needs_human_review` |
| `drafting` | Draft content being prepared | `ready_for_approval`, `needs_human_review` |
| `ready_for_approval` | Operator can edit and approve | `sent`, `needs_human_review`, `dismissed` |
| `needs_human_review` | Evidence or confidence is insufficient | `sent`, `dismissed` |
| `sent` | Approved outward communication completed | terminal |
| `dismissed` | Operator closed the exception | terminal |

Terminal states must reject further transitions.

## 7. Functional requirements

### FR-1: Ingestion and idempotency

- Accept `raw`, `channel`, and optional source metadata.
- Normalize whitespace and case before computing a SHA-256 idempotency key.
- Treat a matching key as a duplicate; increment a duplicate counter and write an activity event.
- Never process a duplicate through triage or investigation.

### FR-2: Structured triage

Triage outputs:

- `reference_id` (nullable)
- `exception_type`
- `severity` from 1 through 5
- `location` (nullable)
- `summary`
- `customer_impact`
- `delay_hours` (nullable)
- `confidence`

Unknown exception types and missing reference IDs must reduce confidence and be routed to review when appropriate.

### FR-3: Bounded investigation

The MVP exposes deterministic tools:

- `lookup_entity(reference_id)` for shipment or job details
- `calculate_eta_impact(reference_id, delay_hours)`
- `get_conditions(location)`

Every call writes a trace item with round, tool name, arguments, result, and any error. The agent must stop after five rounds and return the best available assessment. Tool failure cannot crash the pipeline.

### FR-4: Assessment and prioritization

Assessment includes impact summary, window status, affected value, confidence, recommended action, rounds used, and trace. Rank open work by tier (`red`, `orange`, `green`), then severity, then creation time.

Tier rules:

- Red: severity 5, missed delivery window with meaningful value, or direct safety/cold-chain risk.
- Orange: material delay or customer impact without red conditions.
- Green: lower-risk work with no imminent customer consequence.

### FR-5: Communication and review

- Create an editable customer email subject and body.
- Create an internal action plan.
- Route cases at or above the configurable confidence threshold to `ready_for_approval`.
- Route lower-confidence and malformed cases to `needs_human_review`.
- An operator must explicitly approve before a record becomes `sent`.

### FR-6: Operator UI

The UI must show:

- Metrics for ingested messages, suppressed duplicates, approval-ready items, review items, sent items, and open value at risk.
- An inbox sorted by risk tier.
- A review tab that does not duplicate inbox widgets.
- Raw input, assessment, trace, editable draft, and action plan on each record.
- Activity log entries for receipt, duplicate suppression, routing, investigation, and approval.
- Reset and replay actions for a fresh demonstration.

## 8. Non-functional requirements

- Deterministic demo output: no API key or network access is needed for the primary scenario.
- Fault isolation: malformed or unexpected input must stay contained to its record.
- Replayability: a full reset plus scenario replay produces the same aggregate counts.
- Traceability: all decision-driving tool outputs are inspectable.
- Performance: replay 32 local seed messages in under five seconds on a typical laptop.
- Accessibility: controls are keyboard reachable and labels explain operational intent.

## 9. Data model

### Exception record

```text
id, message_id, raw, channel, triage, tier, status,
assessment, draft, created_at
```

### Triage result

```text
reference_id, exception_type, location, severity,
summary, customer_impact, delay_hours, confidence
```

### Assessment

```text
impact_summary, window_missed, affected_value, confidence,
recommended_action, rounds_used, trace[]
```

### Draft

```text
email_subject, email_body, action_plan
```

## 10. Error handling and guardrails

- Malformed messages become a visible review record with the raw payload preserved.
- Duplicate suppression takes place before triage.
- Agent and tool exceptions degrade to human review, never application failure.
- Outbound delivery is represented as a human-approved state in the MVP; it does not send real email.
- State persistence failures must fall back to a usable in-memory session rather than block the desk.

## 11. Seed scenario

The initial scenario is the Savannah storm described in `docs/seed-data-spec.md`. It contains 32 messages, including three exact duplicates, a malformed feed, varied channels, and a priority pharma shipment. The seed data is fictional and contains no personal information.

## 12. Test plan

Unit tests cover normalization/idempotency, structured triage, tiering, bounded investigation, confidence routing, and terminal state protection.

Integration tests cover message-to-record lifecycle, persistent state round-trip, and exception recovery.

A replay test validates expected aggregate counts and confirms the pharma shipment is the highest-risk open record.

## 13. Milestones

1. Scaffold package, models, test runner, and configuration.
2. Implement ingestion, idempotency, and triage contract.
3. Implement investigation tools, traces, limits, and assessment.
4. Implement draft composer, routing, and state transitions.
5. Build the operator inbox and review UI.
6. Add seed replay, persistence, regression tests, and demo script.

## 14. Future work

Connect EDI 214/315 feeds, email ingestion, and signed webhook events. Add authentication, real delivery integrations, tenant-level customer communication preferences, and feedback loops from review outcomes to improve confidence routing.