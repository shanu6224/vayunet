"""
Facade module exposing risk engine calculations from app.services.risk_engine.
"""
from app.services.risk_engine import (
    calculate_anomaly_and_risk,
    movement_from_wind,
    find_hotspot_location,
    generate_exposure_zone
)

__all__ = [
    "calculate_anomaly_and_risk",
    "movement_from_wind",
    "find_hotspot_location",
    "generate_exposure_zone"
]
