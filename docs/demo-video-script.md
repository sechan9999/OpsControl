# OpsControl Demo Video Script (under 3 minutes)

## 0:00-0:20 | Hook

**Screen:** Empty OpsControl desk, then click **Replay the Savannah storm (32 messages)**.

**Narration:**

"When a port disruption hits, a small operations team can receive dozens of status messages at once. OpsControl turns that flood into a prioritized decision queue, instead of another unstructured inbox."

## 0:20-1:15 | The operator workflow

**Screen:** Point to metrics. Open the top red Inbox item, `OPS-40045-A`.

**Narration:**

"This scenario has 32 messages. OpsControl accepts 29 unique updates and suppresses three duplicate deliveries. The top risk is a temperature-sensitive pharma shipment with a missed delivery window and $25,000 at risk."

"The operator can inspect the raw update, impact assessment, bounded investigation trace, customer draft, and internal action plan. The draft is editable, but a human must approve before it is marked sent."

**Screen:** Edit a word in the subject, then click **Approve & send**.

## 1:15-1:55 | Guardrails

**Screen:** Open **Human review**. Then click **Replay again (all duplicates)** and point to the duplicate metric.

**Narration:**

"OpsControl is designed around safe failure modes. Ambiguous or malformed messages route to Human review instead of being guessed. Every investigation is limited to five rounds. And when the exact storm is replayed, it creates no new operational work; the duplicate counter rises instead."

## 1:55-2:35 | Codex and GPT-5.6

**Screen:** Activity log, then a brief view of the repository README or tests.

**Narration:**

"I used Codex to build the workflow, replay harness, persistence behavior, and regression tests. The public demo uses deterministic triage, so judges get a reliable experience without credentials. OpsControl also includes an opt-in GPT-5.6 structured-triage path for live carrier messages, with a safe fallback when the live request is unavailable."

## 2:35-2:55 | Close

**Screen:** Return to the Inbox and metrics.

**Narration:**

"OpsControl does not replace operator judgment. It gives teams a smaller, prioritized set of decisions, evidence for each one, and customer communication ready for human approval."

## Recording notes

- Keep the final upload public and under three minutes.
- Record at 100% browser zoom and reset the desk before each take.
- Cut loading, typing, silence, and restarts.
- Say both "Codex" and "GPT-5.6" clearly.