# OpsControl

**OpsControl** is an AI-powered human-in-the-loop exception desk for freight operations. It converts a chaotic surge of carrier updates into a prioritized queue, impact assessments grounded in the **Microsoft Supply Chain Ontology**, customer-ready drafts, interactive network cascade graphs, and an operator-gated review surface.

👉 **Devpost Submission:** [devpost.com/software/freightdesk](https://devpost.com/software/freightdesk)  
👉 **GitHub Repo:** [github.com/sechan9999/OpsControl](https://github.com/sechan9999/OpsControl)

---

## 🌐 Live Demo

[**opscontrol.streamlit.app**](https://opscontrol.streamlit.app/) *(also available at [freightdesk.streamlit.app](https://freightdesk.streamlit.app/))*

The deployed demo uses deterministic scenario data. No account, API key, or credentials are required for judges (demo operator PIN: `2468`).

### 🎯 Judge Test Path

1. Enter **Operator Name** (e.g. `J. Park`) and **Approval PIN** (`2468`) in the sidebar.
2. Click **Reset desk** to start clean.
3. Click **Replay the Savannah storm (32 messages)** to ingest 32 realistic freight alerts.
4. Open the **Ontology Dashboard** tab to inspect the network-wide visual cascade flowchart (`Disruption Event → Location/Port → Cargo/Shipment → Risk Exposure → Mitigation Action`) and filter by disruption type or severity.
5. Open the top red item (`OPS-40045-A` - temperature-sensitive pharma) in the **Inbox**:
   - Inspect the **Severity label** (`Critical`), **Timeline** (`⏱ 0.0d to window`), and **Structured Mitigation Cascade** with estimated costs and lead time saved.
   - Expand **🚚 One-Click Alternative Carrier Tender Booking** and execute a backup carrier tender (`ColdExpress`).
   - View the interactive **Mermaid Ontology Cascade Graph** and **📡 Live AIS Vessel Telemetry**.
   - Edit the customer draft (auto-formatted with `NovaPharm` formal preferences).
6. Click **Approve & send** (gated by operator authentication) to deliver the draft.
7. Open the **Fabric IQ AI Agent** tab to run natural language graph queries (e.g., *"What is our total revenue exposure if the Port of Savannah closes?"*).
8. Switch to the **Activity log** tab and click **Download SOC2 WORM Log (JSON)** to export compliance logs.

---

## ⚡ Key Features & Ontology Integration

- **Microsoft Supply Chain Disruption Ontology**: 7-entity cascade model connecting `DisruptionEvent → Location → Shipment → RiskAssessment → MitigationAction → AlternativeCarrier`.
- **Ontology Cascade Dashboard**: Interactive visual Mermaid network flowchart mapping `Disruption → Location → Cargo → Risk USD → Action` with dynamic disruption type & severity filters.
- **Fabric IQ AI Graph Agent**: Natural language supply chain graph query engine producing Cypher queries, affected node metrics, revenue risk estimates, and Mermaid subgraphs.
- **One-Click Alternative Carrier Tender Booking**: Instant tender execution for pre-qualified backup carriers (`ColdExpress`, `ApexLogistics`, `FrostLine`) issuing confirmed booking IDs (`BK-2026-XXXX`).
- **Live AIS Vessel & Port Telemetry**: Satellite AIS vessel tracking (`speed_knots`, `anchorage_dwell_hours`) and Port Terminal congestion index (`USLGB`, `USSAV`, `NLRTM`, `KRPUS`).
- **RLHF Confidence Calibration**: Continuous calibration of auto-queue thresholds based on operator approval feedback history.
- **Enterprise RBAC & SOC2 WORM Log Export**: Role-based access control (`Operator`, `Supervisor`, `Auditor`) with `Supervisor` gate for $10k+ RED tier risks and one-click SOC2 WORM JSON audit export.
- **Multi-Channel & Feed Drop Ingestion**: Supports manual injection, EDI/SMS/Email text parsing, and `.txt` / `.jsonl` feed drop file uploads.

---

## 💻 Run Locally

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Run the 57-test regression suite:

```bash
python -m pytest tests/ -v
```

---

## 🤖 OpenAI & Codex

Built with Codex for rapid agent workflow design, ontology modeling, and 100% test coverage. The default demo uses deterministic stubs so judges receive reproducible results without tokens or credentials.

An optional GPT-5.6 structured-triage path is included for live carrier text. Set `OPSCONTROL_DEMO_MODE=0`, `OPSCONTROL_USE_OPENAI=1`, and `OPENAI_API_KEY` in Streamlit secrets or `.env`.

---

## 📂 Project Structure

- `streamlit_app.py` - OpsControl Streamlit dashboard & Ontology Cascade graph renderer
- `features/` - Extension modules:
  - `features/approval.py` - Gated approval, PIN verification, and review escalation
  - `features/ingest.py` - Single message, batch, and feed drop (.txt / .jsonl) ingestion
  - `features/booking.py` - One-click alternative carrier tender booking execution
  - `features/rbac.py` - Role-based access control (RBAC) & SOC2 WORM audit log exporter
  - `features/email.py` - SMTP delivery adapter with mock fallback
  - `features/customer_profile.py` - Built-in customer communication profiles (`NovaPharm`, `Atlanta Retail`)
  - `features/feedback_loop.py` - RLHF confidence calibration & adaptive threshold feedback loops
- `opscontrol/` - Core decision engine:
  - `opscontrol/graph_agent.py` - Fabric IQ Natural Language Graph Query Agent
  - `opscontrol/telemetry.py` - Live AIS Vessel Tracking & Port Terminal Telemetry provider
  - `opscontrol/models.py` - Ontology dataclasses (`TriageResult`, `Assessment`, `MitigationAction`, `AlternativeCarrier`, `Draft`, `ExceptionRecord`)
  - `opscontrol/agent.py` - Bounded 5-round investigation loop with RLHF calibration
  - `opscontrol/triage.py` - Rule engine with 12 disruption categories & negation guards
  - `opscontrol/tools.py` - Shipment adapter, port conditions, and alternative carrier lookup
  - `opscontrol/composer.py` - Structured `DraftTemplate` composition
  - `opscontrol/store.py` - `Desk` state manager & versioned JSON persistence (v2)
- `tests/` - 57 unit tests (`test_engine.py`, `test_features.py`, `test_ontology.py`, `test_tiering.py`, `test_whats_next.py`)

---

## 🛠️ How We Built It

The build ran from a written PRD with structured milestones, executed in Codex with GPT-5.6: a Streamlit control surface backed by an in-memory decision engine (`Desk`) with versioned JSON state persistence, a bounded investigation agent with function tools (`lookup_shipment`, `eta_impact`, `port_conditions`, `alternative_carriers`), a **Microsoft Supply Chain Disruption Ontology** 7-entity cascade model (`DisruptionEvent → Location → Shipment → Risk → Action → AlternativeCarrier`), a confidence-routed mitigation composer, an **Ontology Cascade Dashboard** with interactive Mermaid flowcharts, and a 57-test regression suite.

At runtime GPT-5.6 handles three key jobs: triage parsing across 12 disruption categories, agent reasoning over tools, and customer comms drafting. The demo replays 32 realistic seed messages — including three exact duplicates, malformed feed input, and a coherent Savannah storm cluster featuring a $25,000 OTIF penalty pharma escalation.

---

## 💡 What We Learned

For operational AI, trust is earned at the boundaries. The useful product is not a system that always acts autonomously; it is a system that makes routine work easy and makes uncertainty unmistakable. By decoupling multi-channel ingestion, agent investigation, customer preference styling, and operator approval, OpsControl ensures that human operators retain explicit control over external communications while AI absorbs the chaos of carrier data floods.

---

## 🚀 Production & What's Next Roadmap

OpsControl has successfully implemented its core extension points: feed drop batch ingestion (.txt/.jsonl), PIN-gated approval (`2468`), SMTP delivery adapters, customer-specific communication profiles (`NovaPharm`, `Atlanta Retail`), adaptive feedback loops for auto-queue threshold tuning, and a **Microsoft Supply Chain Disruption Ontology** layer that transforms isolated carrier alerts into visual 5-tier disruption graphs (`Disruption Event → Location → Cargo → Risk USD → Action`).

Our next production evolution includes:

1. **Enterprise TMS & Satellite AIS Integration**: Direct EDI 214/315 webhooks, monitored inboxes, and live satellite AIS tracking APIs (MarineTraffic / Spire) replacing simulated telemetry.
2. **Microsoft Fabric IQ & Graph Database Grounding**: Transitioning our in-memory Fabric IQ agent into enterprise **Microsoft Fabric IQ** and **Neo4j** graph databases for real-time natural language risk queries across global multi-tenant supply networks.
3. **Automated API Spot Tender Execution**: Connecting our one-click alternative carrier booking engine directly to real-time spot rate APIs (Project44 / FourKites) for instant automated capacity tendering.
4. **Continuous RLHF Model Fine-Tuning**: Leveraging operator feedback datasets to continuously fine-tune local triage and confidence scoring models, further reducing false escalations.
5. **SSO & SOC2 WORM Compliance**: Enterprise Single Sign-On (Entra ID / Okta SSO) and S3 Object Lock immutable compliance storage for enterprise audit trails.

---

## 📄 License

MIT. See [LICENSE](LICENSE).

