# Devpost submission: FreightDesk (OpsControl)

## Project name

FreightDesk (OpsControl)

## Elevator pitch

FreightDesk turns a flood of carrier alerts into a prioritized operations queue, ontology-grounded impact assessments, customer-ready drafts, and a PIN-gated human review desk.

## Project description

### The problem

A port crisis or weather event generates dozens of EDI updates, carrier emails, and driver SMS alerts in minutes. Operations teams struggle to identify affected shipments, estimate financial damage, prioritize critical loads, and communicate timely updates to customers. Duplicates and corrupted feeds make manual spreadsheet management exhausting and error-prone.

### The solution

FreightDesk is an AI-powered human-in-the-loop exception desk for freight operations. It ingests multi-channel carrier feeds, triages exceptions across 12 disruption categories, investigates impact via a bounded evidence loop, models mitigation cascades using the **Microsoft Supply Chain Disruption Ontology**, and drafts customer communications.

High-confidence cases move to **Inbox** (Ready for approval). Ambiguous, malformed, or low-confidence cases move to **Human review**. Operators authenticate with Name + PIN (`2468`), inspect raw messages, agent traces, and interactive **Mermaid Ontology Cascade Graphs**, edit drafts, and explicitly approve before messages are sent.

The Savannah storm replay contains 32 realistic messages: 29 unique records, three duplicate deliveries, malformed input, and a temperature-sensitive pharma escalation with a missed window and $25,000 at risk.

### Guardrails & Reliability

FreightDesk treats reliability as a core product requirement:

- **Idempotency**: SHA-256 hash deduplication prevents duplicate carrier updates from cluttering queues.
- **Bounded Investigation**: Agent loops are hard-capped at 5 tool rounds with full audit traces.
- **Ontology Grounding**: Uses the 7-entity Microsoft Supply Chain Disruption Ontology to trace `DisruptionEvent → Location → Shipment → Risk → Action → AlternativeCarrier`.
- **Authenticated Human Gate**: Operator Name + PIN authentication enforces human oversight before delivery.
- **Adaptive Thresholds**: Human review feedback dynamically tunes auto-queue thresholds (-0.05 / +0.05).
- **Safe Failure Fallbacks**: Malformed or unparseable input routes to Human review; live LLM failures fall back to deterministic stubs.

### How Codex and GPT-5.6 were used

Codex was used to design the workflow, build the 51-test regression suite, implement ontology models, and create Streamlit UI components. The default demo uses deterministic stubs so judges receive zero-token, reproducible results without API keys.

FreightDesk also includes an opt-in GPT-5.6 structured-triage path for live carrier text (`OPSCONTROL_USE_OPENAI=1`), falling back safely to deterministic stubs if the API request fails.

---

## 🔮 What's Next for FreightDesk

While FreightDesk is fully functional today with deterministic demo data, our roadmap focuses on expanding enterprise automation and supply chain intelligence:

### 1. Live Carrier TMS & AIS Vessel Integration
- Direct webhook ingestion for real-time EDI 214/315 carrier status updates.
- Integration with satellite AIS vessel tracking (MarineTraffic/Spire) and port terminal APIs (Savannah, Long Beach, Rotterdam) for live dwell time and weather telemetry.

### 2. Microsoft Fabric IQ & Graph Database Grounding
- Transitioning in-memory ontology models to **Microsoft Fabric IQ** and **Neo4j** graph databases.
- Enabling natural language supply chain risk queries via AI Data Agents (e.g., *"What is our total revenue exposure if the Port of Busan closes for 3 days?"*).

### 3. API-Driven Automated Alternative Carrier Booking
- Extending `MitigationAction` recommendations with direct API spot-rate booking.
- One-click execution to auto-tender secondary carrier capacity (`AlternativeCarrier`) when lead time is at risk.

### 4. Machine Learning RLHF Threshold Optimization
- Training machine learning models on operator approval/rejection feedback to continuously refine triage confidence scores and eliminate false escalations.

### 5. Multi-Tenant Enterprise RBAC & SOC2 Compliance
- Enterprise single sign-on (SSO via Entra ID / Okta), granular role-based access control (RBAC), multi-operator PIN audit trails, and immutable WORM event logging for regulatory compliance.

---

## Private judge access field

No credentials, account, or API key are required for the demo (demo PIN: `2468`).

**Target App URL**: [https://freightdesk.streamlit.app/](https://freightdesk.streamlit.app/) *(mirror: [https://opscontrol.streamlit.app/](https://opscontrol.streamlit.app/))*  
**GitHub Repository**: [https://github.com/sechan9999/OpsControl](https://github.com/sechan9999/OpsControl)  
**Devpost Submission**: [https://devpost.com/software/freightdesk](https://devpost.com/software/freightdesk)

### Judge Test Path

1. Enter **Name** (`J. Park`) and **Approval PIN** (`2468`) in the sidebar.
2. Click **Reset desk** → **Replay the Savannah storm (32 messages)**.
3. Open `OPS-40045-A` in the **Inbox** to inspect assessment, timeline, mitigation actions, and Mermaid cascade graph.
4. Click **Approve & send** to deliver the customer draft (auto-formatted with `NovaPharm` preferences).
5. Switch to **Disruption map** tab to view network-wide disruption impact.
6. Open **Human review** to see low-confidence / malformed cases safely escalated.
7. Click **Replay again (all duplicates)** to verify idempotency (zero duplicate records).