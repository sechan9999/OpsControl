"""Direct unit tests for the tiering.tier() pure function.

Covers all documented PRD rules including boundary values that are not
exercised by the broader pipeline tests.
"""
import pytest

from opscontrol.tiering import tier


# ---- RED conditions -------------------------------------------------------

def test_tier_red_high_severity():
    """Severity >= 4 alone is RED regardless of window or value."""
    assert tier(4, False, 0) == "red"
    assert tier(5, False, 0) == "red"


def test_tier_red_window_missed_with_high_value():
    """Window missed + value >= $10k triggers RED."""
    assert tier(2, True, 10_000) == "red"
    assert tier(2, True, 25_000) == "red"


def test_tier_red_severity_4_with_window_missed():
    """Severity 4 + window missed: still RED (severity rule fires first)."""
    assert tier(4, True, 0) == "red"


# ---- ORANGE conditions ----------------------------------------------------

def test_tier_orange_severity_3():
    """Severity 3 without window miss is ORANGE."""
    assert tier(3, False, 0) == "orange"


def test_tier_orange_window_missed_low_value():
    """Window missed + value below $10k threshold is ORANGE, not RED."""
    assert tier(2, True, 9_999) == "orange"
    assert tier(2, True, 0) == "orange"
    assert tier(1, True, 500) == "orange"


def test_tier_orange_severity_3_window_missed_low_value():
    """Severity 3 with missed window but low value: ORANGE (value < $10k)."""
    assert tier(3, True, 5_000) == "orange"


# ---- GREEN conditions -----------------------------------------------------

def test_tier_green_low_severity_no_miss():
    """Severity <= 2 with no window miss and no value is GREEN."""
    assert tier(1, False, 0) == "green"
    assert tier(2, False, 0) == "green"


def test_tier_green_high_value_no_window_miss():
    """High value alone without a missed window is not enough for RED/ORANGE."""
    assert tier(2, False, 100_000) == "green"


# ---- Exact boundary values ------------------------------------------------

@pytest.mark.parametrize("value,expected", [
    (9_999, "orange"),
    (10_000, "red"),
    (10_001, "red"),
])
def test_tier_boundary_at_10k(value, expected):
    """$10,000 is the exact threshold between ORANGE and RED for missed windows."""
    assert tier(2, True, value) == expected


@pytest.mark.parametrize("severity,expected", [
    (3, "orange"),
    (4, "red"),
])
def test_tier_severity_boundary_3_vs_4(severity, expected):
    """Severity 3 is ORANGE; severity 4 is RED."""
    assert tier(severity, False, 0) == expected
