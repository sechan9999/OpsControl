# Devpost submission: OpsControl

## Project name

OpsControl

## Elevator pitch

OpsControl turns a flood of carrier alerts into a prioritized operations queue, ontology-grounded impact assessments, customer-ready drafts, and a PIN-gated human review desk.

## Project description

### The problem

A port crisis or weather event generates dozens of EDI updates, carrier emails, and driver SMS alerts in minutes. Operations teams struggle to identify affected shipments, estimate financial damage, prioritize critical loads, and communicate timely updates to customers. Duplicates and corrupted feeds make manual spreadsheet management exhausting and error-prone.

### The solution

OpsControl is an AI-powered human-in-the-loop exception desk for freight operations. It ingests multi-channel carrier feeds, triages exceptions across 12 disruption categories, investigates impact via a bounded evidence loop, models mitigation cascades using the **Microsoft Supply Chain Disruption Ontology**, and drafts customer communications.

High-confidence cases move to **Inbox** (Ready for approval). Ambiguous, malformed, or low-confidence cases move to **Human review**. Operators authenticate with Name + PIN (`2468`), inspect raw messages, agent traces, live AIS vessel telemetry, and interactive **Mermaid Ontology Cascade Graphs**, edit drafts, and explicitly approve before messages are sent.

The Savannah storm replay contains 32 realistic messages: 29 unique records, three duplicate deliveries, malformed input, and a temperature-sensitive pharma escalation with a missed window and $25,000 at risk.

### Guardrails & Reliability

OpsControl treats reliability as a core product requirement:

- **Idempotency**: SHA-256 hash deduplication prevents duplicate carrier updates from cluttering queues.
- **Bounded Investigation**: Agent loops are hard-capped at 5 tool rounds with full audit traces.
- **Ontology Grounding**: Uses the 7-entity Microsoft Supply Chain Disruption Ontology to trace `DisruptionEvent → Location → Shipment → Risk → Action → AlternativeCarrier`.
- **Ontology Dashboard**: Interactive visual Mermaid network flowchart mapping `Disruption → Location → Cargo → Risk USD → Action` with dynamic disruption type & severity filters.
- **Fabric IQ AI Graph Agent**: Natural language graph queries (Cypher queries, node counts, revenue risk, and subgraphs).
- **One-Click Carrier Booking**: Instant tender execution for backup carriers (`ColdExpress`, `ApexLogistics`) issuing confirmed booking IDs (`BK-2026-XXXX`).
- **Authenticated Human Gate & RBAC**: Operator Name + PIN authentication with `Supervisor` gate for $10k+ RED tier risks.
- **Adaptive Thresholds & RLHF Calibration**: Human review feedback dynamically tunes auto-queue thresholds (-0.05 / +0.05) and calibrates model confidence.
- **Safe Failure Fallbacks**: Malformed or unparseable input routes to Human review; live LLM failures fall back to deterministic stubs.

### How Codex and GPT-5.6 were used

Codex was used to design the workflow, build the 57-test regression suite, implement ontology models, and create Streamlit UI components. The default demo uses deterministic stubs so judges receive zero-token, reproducible results without API keys.

OpsControl also includes an opt-in GPT-5.6 structured-triage path for live carrier text (`OPSCONTROL_USE_OPENAI=1`), falling back safely to deterministic stubs if the API request fails.

---

## What we learned

For operational AI, trust is earned at the boundaries. The useful product is not a system that always acts autonomously; it is a system that makes routine work easy and makes uncertainty unmistakable. By decoupling multi-channel ingestion, agent investigation, customer preference styling, and operator approval, OpsControl ensures that human operators retain explicit control over external communications while AI absorbs the chaos of carrier data floods.

---

## What's next for OpsControl

OpsControl has successfully implemented its core extension points: feed drop batch ingestion (.txt/.jsonl), PIN-gated approval (`2468`), SMTP delivery adapters, customer-specific communication profiles (`NovaPharm`, `Atlanta Retail`), adaptive feedback loops for auto-queue threshold tuning, and a **Microsoft Supply Chain Disruption Ontology** layer that transforms isolated carrier alerts into visual 5-tier disruption graphs (`Disruption Event → Location → Cargo → Risk USD → Action`).

Our next production evolution includes:

1. **Enterprise TMS & Satellite AIS Integration**: Direct EDI 214/315 webhooks, monitored inboxes, and live satellite AIS tracking APIs (MarineTraffic / Spire) replacing simulated telemetry.
2. **Microsoft Fabric IQ & Graph Database Grounding**: Transitioning our in-memory Fabric IQ agent into enterprise **Microsoft Fabric IQ** and **Neo4j** graph databases for real-time natural language risk queries across global multi-tenant supply networks.
3. **Automated API Spot Tender Execution**: Connecting our one-click alternative carrier booking engine directly to real-time spot rate APIs (Project44 / FourKites) for instant automated capacity tendering.
4. **Continuous RLHF Model Fine-Tuning**: Leveraging operator feedback datasets to continuously fine-tune local triage and confidence scoring models, further reducing false escalations.
5. **SSO & SOC2 WORM Compliance**: Enterprise Single Sign-On (Entra ID / Okta SSO) and S3 Object Lock immutable compliance storage for enterprise audit trails.

---

## Private judge access field

No credentials, account, or API key are required for the demo (demo PIN: `2468`).

**Target App URL**: [https://opscontrol.streamlit.app/](https://opscontrol.streamlit.app/) *(mirror: [https://freightdesk.streamlit.app/](https://freightdesk.streamlit.app/))*  
**GitHub Repository**: [https://github.com/sechan9999/OpsControl](https://github.com/sechan9999/OpsControl)  
**Devpost Submission**: [https://devpost.com/software/freightdesk](https://devpost.com/software/freightdesk)

### Judge Test Path

1. Enter **Name** (`J. Park`) and **Approval PIN** (`2468`) in the sidebar.
2. Click **Reset desk** → **Replay the Savannah storm (32 messages)**.
3. Open the **Ontology Dashboard** tab to view network-wide disruption cascades and filter by type or severity.
4. Open `OPS-40045-A` in the **Inbox** to inspect assessment, timeline, mitigation actions, and Mermaid cascade graph.
5. Expand **🚚 One-Click Alternative Carrier Tender Booking** and execute a backup carrier tender (`ColdExpress`).
6. Click **Approve & send** to deliver the customer draft (auto-formatted with `NovaPharm` preferences).
7. Open **Fabric IQ AI Agent** tab to query supply chain exposure in natural language.
8. Switch to **Activity log** tab and click **Download SOC2 WORM Log (JSON)** to export audit trails.