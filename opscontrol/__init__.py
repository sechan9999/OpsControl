"""OpsControl — core freight exception processing package.

Public modules
--------------
agent       Bounded investigation loop (up to N tool rounds).
composer    Customer email draft composition with DraftTemplate.
config      Settings dataclass and environment-based factory.
models      Core data model: TriageResult, Assessment, Draft, ExceptionRecord.
pipeline    End-to-end message processor (dedup → triage → investigate → compose → route).
store       In-memory Desk with optional JSON snapshot persistence.
tiering     RED/ORANGE/GREEN priority classifier (pure function).
tools       ShipmentAdapter protocol + MockShipmentAdapter + module-level helpers.
triage      Keyword-rule triage engine with optional GPT-5.6 structured-output path.
"""

__all__ = [
    "agent",
    "composer",
    "config",
    "models",
    "pipeline",
    "store",
    "tiering",
    "tools",
    "triage",
]
