"""Operator-facing OpsControl feature modules.

These modules provide stable extension points around the core workflow without
coupling external integrations directly to the Streamlit application.
"""

__all__ = [
    "approval",
    "customer_profile",
    "email",
    "feedback_loop",
    "ingest",
]
