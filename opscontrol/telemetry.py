import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class AISVesselTelemetry:
    mmsi: str
    vessel_name: str
    flag: str
    speed_knots: float
    destination_port: str
    eta_utc: str
    lat: float
    lon: float
    anchorage_dwell_hours: float
    status: str  # Underway, Anchored, Moored, Drifting


@dataclass(frozen=True)
class PortTerminalTelemetry:
    port_name: str
    code: str
    congestion_index: float  # 0.0 - 1.0
    quay_cranes_operating: int
    avg_dwell_days: float
    weather_condition: str
    wind_knots: float
    terminal_status: str  # Normal, Heavy Congestion, Gate Suspended, Severe Weather


PORT_TELEMETRY = {
    "Port of Savannah": PortTerminalTelemetry(
        port_name="Port of Savannah", code="USSAV", congestion_index=0.88,
        quay_cranes_operating=14, avg_dwell_days=4.2, weather_condition="Severe Rain",
        wind_knots=32.0, terminal_status="Heavy Congestion",
    ),
    "Long Beach": PortTerminalTelemetry(
        port_name="Port of Long Beach", code="USLGB", congestion_index=0.45,
        quay_cranes_operating=22, avg_dwell_days=1.8, weather_condition="Clear",
        wind_knots=10.0, terminal_status="Normal",
    ),
    "Rotterdam": PortTerminalTelemetry(
        port_name="Port of Rotterdam", code="NLRTM", congestion_index=0.72,
        quay_cranes_operating=18, avg_dwell_days=3.1, weather_condition="Gale Wind",
        wind_knots=42.0, terminal_status="Heavy Congestion",
    ),
    "Busan New Port": PortTerminalTelemetry(
        port_name="Busan New Port", code="KRPUS", congestion_index=0.20,
        quay_cranes_operating=28, avg_dwell_days=1.1, weather_condition="Clear",
        wind_knots=8.0, terminal_status="Normal",
    ),
}


KNOWN_VESSELS = {
    "OPS-40021-A": AISVesselTelemetry(
        mmsi="367123450", vessel_name="MV Blue Ocean Trader", flag="US",
        speed_knots=0.2, destination_port="Port of Savannah", eta_utc="2026-07-23T14:00:00Z",
        lat=32.0835, lon=-81.0998, anchorage_dwell_hours=28.5, status="Anchored",
    ),
    "OPS-40026-C": AISVesselTelemetry(
        mmsi="563098760", vessel_name="MV Ever Star", flag="SG",
        speed_knots=18.4, destination_port="Long Beach", eta_utc="2026-07-25T08:00:00Z",
        lat=28.4500, lon=-135.2000, anchorage_dwell_hours=0.0, status="Underway",
    ),
    "OPS-40045-A": AISVesselTelemetry(
        mmsi="368999110", vessel_name="MV Polar Express", flag="US",
        speed_knots=0.0, destination_port="Port of Savannah", eta_utc="2026-07-23T08:00:00Z",
        lat=32.1200, lon=-81.1300, anchorage_dwell_hours=18.0, status="Moored",
    ),
}


def get_vessel_telemetry(shipment_ref: str | None) -> Optional[AISVesselTelemetry]:
    if not shipment_ref:
        return None
    if shipment_ref in KNOWN_VESSELS:
        return KNOWN_VESSELS[shipment_ref]

    # Generate synthetic telemetry deterministically for unknown ref
    h = int(hashlib.md5(shipment_ref.encode()).hexdigest(), 16)
    vessel_name = f"MV Carrier-{shipment_ref[-3:]}"
    speed = round(12.0 + (h % 10), 1)
    status = "Underway" if speed > 5.0 else "Anchored"
    return AISVesselTelemetry(
        mmsi=str(300000000 + (h % 699999999)),
        vessel_name=vessel_name,
        flag=["US", "SG", "LR", "PA"][h % 4],
        speed_knots=speed,
        destination_port="Port of Savannah",
        eta_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        lat=32.0 + (h % 100) / 100.0,
        lon=-81.0 - (h % 100) / 100.0,
        anchorage_dwell_hours=float(h % 36),
        status=status,
    )


def get_port_telemetry(location: str | None) -> Optional[PortTerminalTelemetry]:
    if not location:
        return None
    loc_clean = location.strip().lower()
    for name, telemetry in PORT_TELEMETRY.items():
        if loc_clean in name.lower() or name.lower() in loc_clean:
            return telemetry
    return PortTerminalTelemetry(
        port_name=location, code="GENERIC", congestion_index=0.50,
        quay_cranes_operating=12, avg_dwell_days=2.5, weather_condition="Clear",
        wind_knots=12.0, terminal_status="Normal",
    )
