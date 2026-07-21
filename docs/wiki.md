# OpsControl Wiki — AI Exception Desk for Freight Operations

OpsControl is an enterprise human-in-the-loop (HITL) freight exception desk application built for real-time disruption monitoring, automated risk assessment grounded in the **Microsoft Supply Chain Disruption Ontology**, alternative carrier tender execution, and operator-gated customer communication delivery.

- 🌐 **Live Application:** [opscontrol.streamlit.app](https://opscontrol.streamlit.app/)
- 💻 **GitHub Repository:** [github.com/sechan9999/OpsControl](https://github.com/sechan9999/OpsControl)
- 🏆 **Devpost Submission:** [devpost.com/software/freightdesk](https://devpost.com/software/freightdesk)

---

## 🏗️ System Architecture & Data Flow

```
   Raw Messages (EDI / Email / SMS / Feed Drops)
                        │
                        ▼
         ┌─────────────────────────────┐
         │ Ingest & Duplicate Guard    │ (features/ingest.py)
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌─────────────────────────────┐
         │ Structured Triage Engine    │ (opscontrol/triage.py)
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌─────────────────────────────┐
         │ Bounded Investigation Loop  │ (opscontrol/agent.py + tools.py)
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌─────────────────────────────┐
         │ 7-Entity Cascade Ontology   │ (Disruption → Location → Shipment →
         │ & Risk Assessment           │  Risk USD → Action → AlternativeCarrier)
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌─────────────────────────────┐
         │  RLHF Confidence Routing    │
         │  - High Conf (>= threshold) │ ──► Approval Inbox
         │  - Low Conf (< threshold)   │ ──► Human Review Queue
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌─────────────────────────────┐
         │ Gated Operator Action Surface│ (streamlit_app.py)
         │ - One-Click Carrier Tender  │ (features/booking.py)
         │ - Fabric IQ AI Graph Agent  │ (opscontrol/graph_agent.py)
         │ - PyDeck Geospatial Map     │ (streamlit_app.py)
         │ - SOC2 Cryptographic Export │ (features/rbac.py)
         └─────────────────────────────┘
```

---

## 🌐 Supply Chain Disruption Ontology

OpsControl models disruption cascades across a 7-entity graph:

$$\text{Disruption Event} \xrightarrow{\text{affects}} \text{Location/Port} \xrightarrow{\text{supplies}} \text{Shipment} \xrightarrow{\text{triggers}} \text{Risk Assessment} \xrightarrow{\text{recommends}} \text{Mitigation Action} \xrightarrow{\text{activates}} \text{Alternative Carrier}$$

- **Disruption Events**: Port closure, reefer temperature failure, customs hold, dockworker strike, cyber attack outage, geopolitical sanction.
- **Location Nodes**: `Port of Savannah (USSAV)`, `Long Beach (USLGB)`, `Rotterdam (NLRTM)`, `Busan (KRPUS)`, `Atlanta Hub`, `Raleigh Yard`, `Memphis Hub`, `Chicago Hub`.
- **Risk Tiers**:
  - `RED`: Severity $\ge 4$ or Risk Exposure $\ge \$10,000$ USD with missed delivery window (Requires Supervisor PIN approval).
  - `ORANGE`: Moderate risk exposure ($\$1,000 - \$10,000$ USD) or window miss.
  - `GREEN`: Low risk, automated monitoring.

---

## ⚡ Core Features & Capabilities

### 1. 🗺️ Interactive PyDeck Geospatial Telemetry
Visualizes global freight nodes, vessel positions, and shipment risks on an interactive 3D map. Node circle radii and colors dynamically scale based on financial value at risk (`RED` / `ORANGE` / `GREEN`).

### 2. 🚚 One-Click Backup Carrier Tender & ROI Calculator
Calculates real-time net financial ROI before tendering pre-qualified backup carriers (`ColdExpress`, `ApexLogistics`, `FrostLine`):
$$\text{Net Benefit} = \text{OTIF Penalty Saved} - \text{Backup Carrier Cost}$$

### 3. 🤖 Microsoft Fabric IQ AI Graph Query Agent
Natural language query engine grounded in the supply chain disruption ontology. Generates Cypher graph traversal queries, Mermaid subgraphs, and performs comparative scenario simulations (*"What-if rerouting via Charleston vs waiting at Savannah"*).

### 4. 📈 RLHF Adaptive Confidence Calibration
Automatically fine-tunes exception queue confidence thresholds based on historical operator approval and escalation feedback.

### 5. 🔒 Cryptographic SOC2 SHA-256 Hash Chain Audit Trail
Ensures tamper-proof immutability for compliance export logs using cryptographic block hash chaining:
$$H_n = \text{SHA256}(n + H_{n-1} + \text{LogEvent})$$

---

## 📂 Repository Structure

| Path | Description |
| :--- | :--- |
| [streamlit_app.py](file:///c:/Users/secha/OpsControl/streamlit_app.py) | Main Streamlit control surface, PyDeck map renderer & Mermaid graph dashboard |
| [opscontrol/agent.py](file:///c:/Users/secha/OpsControl/opscontrol/agent.py) | Bounded 5-round investigation agent loop |
| [opscontrol/triage.py](file:///c:/Users/secha/OpsControl/opscontrol/triage.py) | Rule-based & GPT-5.6 triage engine across 12 disruption categories |
| [opscontrol/graph_agent.py](file:///c:/Users/secha/OpsControl/opscontrol/graph_agent.py) | Microsoft Fabric IQ Cypher graph query & scenario simulation engine |
| [opscontrol/models.py](file:///c:/Users/secha/OpsControl/opscontrol/models.py) | Dataclasses (`TriageResult`, `Assessment`, `MitigationAction`, `AlternativeCarrier`, `Draft`, `ExceptionRecord`) |
| [opscontrol/store.py](file:///c:/Users/secha/OpsControl/opscontrol/store.py) | In-memory `Desk` state manager & versioned JSON persistence |
| [opscontrol/telemetry.py](file:///c:/Users/secha/OpsControl/opscontrol/telemetry.py) | Live satellite AIS vessel tracking and port congestion telemetry |
| [features/approval.py](file:///c:/Users/secha/OpsControl/features/approval.py) | Gated PIN-verified approval, review escalation, and dismissal |
| [features/booking.py](file:///c:/Users/secha/OpsControl/features/booking.py) | One-click alternative carrier tender booking & ROI tradeoff calculator |
| [features/rbac.py](file:///c:/Users/secha/OpsControl/features/rbac.py) | Role-based access control (`Operator`, `Supervisor`, `Auditor`) & SOC2 WORM cryptographic log exporter |
| [features/feedback_loop.py](file:///c:/Users/secha/OpsControl/features/feedback_loop.py) | RLHF adaptive threshold tuning feedback loop |
| [features/ingest.py](file:///c:/Users/secha/OpsControl/features/ingest.py) | Single message, batch, and feed drop (.txt / .jsonl) ingestion adapters |
| `tests/` | 60-test regression suite (`test_engine.py`, `test_features.py`, `test_ontology.py`, `test_tiering.py`, `test_improvements.py`, `test_whats_next.py`) |

---

## 🧪 Testing & Quality Assurance

Run the 60-test regression suite:
```bash
python -m pytest tests/ -v
```
- **Total Tests:** 60 passed in 0.15s.
- **Coverage:** 100% pass rate across engine triage, tiering, ontology cascade, carrier booking, Fabric IQ agent, and cryptographic audit log verification.
