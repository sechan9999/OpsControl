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

## 🚀 Production Integration Path

OpsControl decouples ingestion, triage, investigation, customer profiling, and delivery into stable extension points. Production deployments can connect:
- **Feeds**: Authenticated EDI 214/315, AIS vessel tracking, and webhook endpoints
- **Delivery**: Transactional SMTP / SendGrid / Postmark servers
- **Graph AI**: Microsoft Fabric IQ / Neo4j for natural language supply chain graph queries
