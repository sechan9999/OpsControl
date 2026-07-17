def tier(severity: int, window_missed: bool, affected_value: float) -> str:
    """PRD section 3/F4 rule. Pure function - keep it boring."""
    if severity >= 4 or (window_missed and affected_value >= 10000):
        return "red"
    if severity == 3 or window_missed:
        return "orange"
    return "green"
