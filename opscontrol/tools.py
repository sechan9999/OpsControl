import hashlib

# Known shipments referenced by the seed data. Unknown refs get a deterministic
# synthetic record so demos and tests are reproducible.
MOCK_SHIPMENTS = {
    "OPS-40021-A": {"carrier": "BlueOcean", "lane": "SAV->ATL", "slack_hours": 30, "order_value_usd": 18000, "commodity": "apparel", "temperature_controlled": False},
    "OPS-40022-B": {"carrier": "BlueOcean", "lane": "SAV->CLT", "slack_hours": 10, "order_value_usd": 22000, "commodity": "furniture", "temperature_controlled": False},
    "OPS-40023-C": {"carrier": "BlueOcean", "lane": "SAV->ATL", "slack_hours": 44, "order_value_usd": 9000, "commodity": "toys", "temperature_controlled": False},
    "OPS-40026-C": {"carrier": "EverLine", "lane": "SIN->LAX", "slack_hours": 96, "order_value_usd": 54000, "commodity": "electronics", "temperature_controlled": False},
    "OPS-40027-A": {"carrier": "PacRim", "lane": "LGB->PHX", "slack_hours": 20, "order_value_usd": 31000, "commodity": "appliances", "temperature_controlled": False},
    "OPS-40029-C": {"carrier": "ColdChain", "lane": "MEM->ORD", "slack_hours": 8, "order_value_usd": 42000, "commodity": "frozen food", "temperature_controlled": True},
    "OPS-40030-A": {"carrier": "Maersk", "lane": "SAV->RTM", "slack_hours": 120, "order_value_usd": 15000, "commodity": "machinery", "temperature_controlled": False},
    "OPS-40036-A": {"carrier": "CMA", "lane": "RTM->DUS", "slack_hours": 60, "order_value_usd": 27000, "commodity": "chemicals", "temperature_controlled": False},
    "OPS-40038-C": {"carrier": "ColdChain", "lane": "MEM->DFW", "slack_hours": 5, "order_value_usd": 38000, "commodity": "dairy", "temperature_controlled": True},
    "OPS-40045-A": {"carrier": "ColdChain", "lane": "SAV->RDU", "slack_hours": 4, "order_value_usd": 25000, "commodity": "pharmaceuticals", "temperature_controlled": True},
}

PORT_CONDITIONS = {
    "port of savannah": {"congestion_level": "severe", "weather": "Severe Rain", "avg_dwell_hours": 22},
    "savannah": {"congestion_level": "severe", "weather": "Severe Rain", "avg_dwell_hours": 22},
    "long beach": {"congestion_level": "moderate", "weather": "Clear", "avg_dwell_hours": 9},
    "rotterdam": {"congestion_level": "high", "weather": "Windy", "avg_dwell_hours": 14},
    "busan new port": {"congestion_level": "low", "weather": "Clear", "avg_dwell_hours": 4},
    "busan": {"congestion_level": "low", "weather": "Clear", "avg_dwell_hours": 4},
    "singapore": {"congestion_level": "moderate", "weather": "Thunderstorms", "avg_dwell_hours": 8},
    "memphis": {"congestion_level": "high", "weather": "Clear", "avg_dwell_hours": 12},
    "norfolk intl": {"congestion_level": "low", "weather": "Clear", "avg_dwell_hours": 3},
    "charleston": {"congestion_level": "moderate", "weather": "Rain", "avg_dwell_hours": 7},
}


def _synthetic_shipment(ref: str) -> dict:
    h = int(hashlib.md5(ref.encode()).hexdigest(), 16)
    return {
        "carrier": ["BlueOcean", "PacRim", "EverLine", "Maersk"][h % 4],
        "lane": "SAV->ATL",
        "slack_hours": 12 + (h % 60),
        "order_value_usd": 5000 + (h % 50) * 1000,
        "commodity": ["apparel", "electronics", "auto parts", "paper"][h % 4],
        "temperature_controlled": False,
    }


def lookup_shipment(ref):
    if not ref:
        return {"error": "missing shipment_ref"}
    return dict(MOCK_SHIPMENTS.get(ref, _synthetic_shipment(ref)), ref=ref)


def eta_impact(ref, delay_hours, slack_hours):
    if not ref:
        return {"error": "missing shipment_ref"}
    delay = float(delay_hours or 0)
    hours_past = max(0.0, delay - float(slack_hours))
    return {
        "delay_hours": delay,
        "window_missed": hours_past > 0,
        "hours_past_window": round(hours_past, 1),
    }


def port_conditions(location):
    if not location:
        return {"error": "missing location"}
    cond = PORT_CONDITIONS.get(location.strip().lower())
    if cond is None:
        return {"congestion_level": "unknown", "weather": "unknown", "avg_dwell_hours": 6}
    return dict(cond)
