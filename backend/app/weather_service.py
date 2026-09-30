"""
Facade module exposing weather services from app.services.weather_service.
"""
from app.services.weather_service import (
    get_weather,
    _fetch_open_meteo,
    _fetch_wttr_in,
    WEATHER_HEADERS
)

__all__ = ["get_weather", "WEATHER_HEADERS"]
