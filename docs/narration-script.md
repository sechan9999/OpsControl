# OpsControl video narration

A disruption should create a prioritized queue, not chaos. OpsControl is a human-in-the-loop exception desk for freight operations. It turns carrier updates, broker emails, and driver alerts into a clear set of operational decisions.

In this Savannah storm scenario, thirty-two updates arrive together. OpsControl accepts twenty-nine unique messages and identifies three duplicate deliveries before they create more work. That is important because carrier systems often redeliver the same status update, especially during a disruption.

The inbox ranks work by consequence. At the top is OPS-40045-A, a temperature-sensitive pharma shipment. The updated arrival misses its hard delivery window, placing twenty-five thousand dollars at risk. Instead of asking an operator to trust a summary, OpsControl keeps the evidence visible. The assessment shows the delivery impact, and the trace records the bounded investigation steps: shipment lookup, port conditions, ETA impact, and final assessment.

OpsControl prepares the customer update and an internal action plan, but it does not send anything automatically. The operator can edit the draft and explicitly approve it. That keeps the person responsible for the final external decision.

The workflow is designed for uncertainty as well as the happy path. A message with no usable shipment reference, or a malformed feed, goes to Human review. The system preserves the raw input and makes the uncertainty visible. It does not invent confidence. Every investigation is capped at five rounds, so a difficult record cannot turn into an unbounded loop.

I used Codex to build the workflow, safety guardrails, replay harness, persistence behavior, and regression tests. The public demonstration uses deterministic triage, so every judge can replay the same scenario without credentials or a network dependency. OpsControl also includes an opt-in GPT-5.6 structured-triage path for live carrier messages. That path is explicitly configured, and it falls back safely if a live request is unavailable.

OpsControl does not replace an operator's judgment. It gives the operator a smaller, risk-ranked set of decisions, inspectable evidence, and communication ready for human approval. The next step is to connect real EDI feeds, email ingestion, and webhook events. Try the demo at opscontrol.streamlit.app.