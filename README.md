# OpsControl

**OpsControl** is an AI-powered human-in-the-loop exception desk for freight operations. It converts a chaotic surge of carrier updates into a prioritized queue, impact assessments grounded in the **Microsoft Supply Chain Ontology**, customer-ready drafts, interactive cascade graphs, and an operator-gated review surface.

👉 **Devpost Submission:** [devpost.com/software/freightdesk](https://devpost.com/software/freightdesk)  
👉 **GitHub Repo:** [github.com/sechan9999/OpsControl](https://github.com/sechan9999/OpsControl)

---

## 🌐 Live Demo

[**freightdesk.streamlit.app**](https://freightdesk.streamlit.app/) *(also available at [opscontrol.streamlit.app](https://opscontrol.streamlit.app/))*

The deployed demo uses deterministic scenario data. No account, API key, or credentials are required for judges (demo operator PIN: `2468`).

### 🎯 Judge Test Path

1. Enter **Operator Name** (e.g. `J. Park`) and **Approval PIN** (`2468`) in the sidebar.
2. Click **Reset desk** to start clean.
3. Click **Replay the Savannah storm (32 messages)** to ingest 32 realistic freight alerts.
4. Open the top red item (`OPS-40045-A` - temperature-sensitive pharma) in the **Inbox**:
   - Inspect the **Severity label** (`Critical`), **Timeline** (`⏱ 0.0d to window`), and **Structured Mitigation Cascade** with estimated costs and lead time saved.
   - View the interactive **Mermaid Ontology Cascade Graph** (`Disruption → Location → Shipment → Risk → Action`).
   - Edit the customer draft (auto-formatted with `NovaPharm` formal preferences).
5. Click **Approve & send** (gated by operator authentication) to deliver the draft.
6. Switch to the **Disruption map** tab to inspect active disruptions across network nodes.
7. Open **Human review** to inspect unclassified or low-confidence updates safely escalated for operator judgment.
8. Click **Replay again (all duplicates)** to verify idempotency (zero duplicate records created).

---

## ⚡ Key Features & Ontology Integration

- **Microsoft Supply Chain Disruption Ontology**: 7-entity cascade model connecting `DisruptionEvent → Location → Shipment → RiskAssessment → MitigationAction → AlternativeCarrier`.
- **Expanded Disruption Types**: Classifies `PORT_DELAY`, `CUSTOMS_HOLD`, `REEFER_TEMP`, `VESSEL_ROLLOVER`, `GEOPOLITICAL` (strikes/sanctions), `CYBER_ATTACK` (ransomware), `FINANCIAL_FAILURE` (carrier bankruptcy), and `PANDEMIC`.
- **Structured Mitigation Actions**: Ranks typed actions (`REROUTE`, `ACTIVATE_ALTERNATIVE_CARRIER`, `EXPEDITE_SHIPMENT`, `CUSTOMS_EXPEDITE`) with cost estimates ($) and lead time saved (days).
- **Idempotency & Deduplication**: SHA-256 hash dedup filters repeated carrier signals without duplicating work.
- **Authenticated Approval Gate**: Operator Name + PIN authentication (`2468`) with audit trail logging (`by=J. Park`).
- **Adaptive Feedback Loop**: Operator approvals/escalations dynamically adjust type-specific confidence thresholds (-0.05 / +0.05).
- **Multi-Channel & Feed Drop Ingestion**: Supports manual injection, EDI/SMS/Email text parsing, and `.txt` / `.jsonl` feed drop file uploads.

---

## 💻 Run Locally

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Run the 51-test regression suite:

```bash
python -m pytest tests/ -v
```

---

## 🤖 OpenAI & Codex

Built with Codex for rapid agent workflow design, ontology modeling, and 100% test coverage. The default demo uses deterministic stubs so judges receive reproducible results without tokens or credentials.

An optional GPT-5.6 structured-triage path is included for live carrier text. Set `OPSCONTROL_DEMO_MODE=0`, `OPSCONTROL_USE_OPENAI=1`, and `OPENAI_API_KEY` in Streamlit secrets or `.env`.

---

## 📂 Project Structure

- `streamlit_app.py` - FreightDesk Streamlit dashboard & interactive cascade graph renderer
- `features/` - Extension modules:
  - `features/approval.py` - Gated approval, PIN verification, and review escalation
  - `features/ingest.py` - Single message, batch, and feed drop (.txt / .jsonl) ingestion
  - `features/email.py` - SMTP delivery adapter with mock fallback
  - `features/customer_profile.py` - Built-in customer communication profiles (`NovaPharm`, `Atlanta Retail`)
  - `features/feedback_loop.py` - Adaptive threshold feedback loops & audit events
- `opscontrol/` - Core decision engine:
  - `opscontrol/models.py` - Ontology dataclasses (`TriageResult`, `Assessment`, `MitigationAction`, `AlternativeCarrier`, `Draft`, `ExceptionRecord`)
  - `opscontrol/agent.py` - Bounded 5-round investigation loop & mitigation action generator
  - `opscontrol/triage.py` - Rule engine with 12 disruption categories & negation guards
  - `opscontrol/tools.py` - Shipment adapter, port conditions, and alternative carrier lookup
  - `opscontrol/composer.py` - Structured `DraftTemplate` composition
  - `opscontrol/store.py` - `Desk` state manager & versioned JSON persistence (v2)
- `tests/` - 51 unit tests (`test_engine.py`, `test_features.py`, `test_ontology.py`, `test_tiering.py`)

---

## 🚀 Production Integration Path

FreightDesk decouples ingestion, triage, investigation, customer profiling, and delivery into stable extension points. Production deployments can connect:
- **Feeds**: Authenticated EDI 214/315, AIS vessel tracking, and webhook endpoints
- **Delivery**: Transactional SMTP / SendGrid / Postmark servers
- **Graph AI**: Microsoft Fabric IQ / Neo4j for natural language supply chain graph queries
