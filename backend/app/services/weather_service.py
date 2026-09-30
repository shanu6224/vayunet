import os
import time
import logging
from typing import Dict, Any, Optional, Tuple
import httpx

logger = logging.getLogger("vayunet.weather")

# In-memory short-term cache for weather data
# Key: (round(lat, 2), round(lon, 2)) -> ~1.1 km spatial cell
# Value: (timestamp, weather_dict)
_WEATHER_CACHE: Dict[Tuple[float, float], Tuple[float, Dict[str, Any]]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

WEATHER_HEADERS = {
    "User-Agent": "VayuNet-Atmospheric-Monitor/1.1 (https://github.com/shanu6224/vayunet; contact@vayunet.app)",
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive"
}

HTTP_TIMEOUT = httpx.Timeout(12.0, connect=5.0)

def _get_from_cache(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    key = (round(lat, 2), round(lon, 2))
    if key in _WEATHER_CACHE:
        ts, data = _WEATHER_CACHE[key]
        if time.time() - ts < CACHE_TTL_SECONDS:
            logger.info(f"Returning cached weather for cell {key} (age: {int(time.time() - ts)}s)")
            return dict(data)
    return None

def _store_in_cache(lat: float, lon: float, data: Dict[str, Any]):
    key = (round(lat, 2), round(lon, 2))
    _WEATHER_CACHE[key] = (time.time(), dict(data))
    # Keep cache size bounded
    if len(_WEATHER_CACHE) > 500:
        oldest_key = min(_WEATHER_CACHE.keys(), key=lambda k: _WEATHER_CACHE[k][0])
        del _WEATHER_CACHE[oldest_key]

async def _fetch_open_meteo(client: httpx.AsyncClient, url: str, lat: float, lon: float, model_name: str) -> Optional[Dict[str, Any]]:
    params = {
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "current": (
            "temperature_2m,relative_humidity_2m,surface_pressure,"
            "wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation"
        ),
        "timezone": "auto",
    }
    try:
        response = await client.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            temp = current.get("temperature_2m")
            humidity = current.get("relative_humidity_2m")
            wind_speed = current.get("wind_speed_10m")
            wind_direction = current.get("wind_direction_10m")
            
            if wind_speed is not None and wind_direction is not None:
                return {
                    "temperature_c": float(temp) if temp is not None else None,
                    "humidity_pct": float(humidity) if humidity is not None else None,
                    "surface_pressure_hpa": float(current.get("surface_pressure")) if current.get("surface_pressure") is not None else None,
                    "wind_speed_kmh": float(wind_speed),
                    "wind_direction_deg": float(wind_direction),
                    "wind_gusts_kmh": float(current.get("wind_gusts_10m")) if current.get("wind_gusts_10m") is not None else None,
                    "precipitation_mm": float(current.get("precipitation")) if current.get("precipitation") is not None else 0.0,
                    "source": f"Open-Meteo ({model_name})"
                }
            else:
                logger.warning(f"Open-Meteo {model_name} response missing wind fields: {current}")
        else:
            logger.warning(
                f"Open-Meteo {model_name} returned status {response.status_code} for ({lat}, {lon}): {response.text[:200]}"
            )
    except httpx.HTTPError as exc:
        logger.warning(f"Open-Meteo {model_name} HTTP error for ({lat}, {lon}): {type(exc).__name__}: {exc}")
    except Exception as exc:
        logger.warning(f"Open-Meteo {model_name} unexpected error for ({lat}, {lon}): {type(exc).__name__}: {exc}")
    return None

async def _fetch_wttr_in(client: httpx.AsyncClient, lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """Zero-authentication fallback weather provider if Open-Meteo rate limit is hit on shared cloud IP."""
    url = f"https://wttr.in/{lat:.4f},{lon:.4f}?format=j1"
    try:
        response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            conditions = data.get("current_condition", [])
            if conditions:
                c = conditions[0]
                temp = c.get("temp_C")
                humidity = c.get("humidity")
                wind_speed = c.get("windspeedKmph")
                wind_dir = c.get("winddirDegree")
                pressure = c.get("pressure")
                if wind_speed is not None and wind_dir is not None:
                    return {
                        "temperature_c": float(temp) if temp is not None else None,
                        "humidity_pct": float(humidity) if humidity is not None else None,
                        "surface_pressure_hpa": float(pressure) if pressure is not None else None,
                        "wind_speed_kmh": float(wind_speed),
                        "wind_direction_deg": float(wind_dir),
                        "wind_gusts_kmh": None,
                        "precipitation_mm": float(c.get("precipMM", 0.0)),
                        "source": "Open-Meteo / wttr.in Fallback"
                    }
        else:
            logger.warning(f"wttr.in returned status {response.status_code} for ({lat}, {lon})")
    except Exception as exc:
        logger.warning(f"wttr.in fallback failed for ({lat}, {lon}): {type(exc).__name__}: {exc}")
    return None

async def get_weather(lat: float, lon: float) -> dict:
    """
    Fetches real-time weather and wind conditions dynamically for given coordinates (lat, lon).
    Extracts:
      - temperature_2m -> temperature_c
      - relative_humidity_2m -> humidity_pct
      - wind_speed_10m -> wind_speed_kmh
      - wind_direction_10m -> wind_direction_deg
      - surface_pressure -> surface_pressure_hpa
    Uses multi-tiered endpoints, custom headers, and short-term spatial caching to prevent 429 errors.
    """
    # 1. Check spatial cache first
    cached = _get_from_cache(lat, lon)
    if cached is not None:
        return cached

    # 2. Setup candidate endpoints
    custom_url = os.getenv("OPEN_METEO_URL")
    endpoints = []
    if custom_url:
        endpoints.append((custom_url.strip(), "Configured"))
    endpoints.extend([
        ("https://api.open-meteo.com/v1/forecast", "Best Match"),
        ("https://api.open-meteo.com/v1/gfs", "GFS"),
        ("https://api.open-meteo.com/v1/dwd-icon", "DWD ICON")
    ])

    last_error = None
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=WEATHER_HEADERS) as client:
        # Try Open-Meteo endpoints
        for url, model_name in endpoints:
            weather = await _fetch_open_meteo(client, url, lat, lon, model_name)
            if weather:
                logger.info(
                    f"Successfully fetched weather via {weather['source']} for ({lat:.4f}, {lon:.4f}): "
                    f"wind={weather['wind_speed_kmh']} km/h @ {weather['wind_direction_deg']}°"
                )
                _store_in_cache(lat, lon, weather)
                return weather
        
        # If Open-Meteo endpoints all failed / 429'd on shared cloud egress IP, try zero-auth fallback
        logger.info(f"Open-Meteo endpoints unavailable for ({lat}, {lon}). Attempting fallback provider...")
        wttr_weather = await _fetch_wttr_in(client, lat, lon)
        if wttr_weather:
            logger.info(
                f"Successfully fetched weather via {wttr_weather['source']} for ({lat:.4f}, {lon:.4f}): "
                f"wind={wttr_weather['wind_speed_kmh']} km/h @ {wttr_weather['wind_direction_deg']}°"
            )
            _store_in_cache(lat, lon, wttr_weather)
            return wttr_weather

    # If all options failed, raise descriptive exception so caller logs and marks unavailable
    err_msg = f"All weather providers (Open-Meteo & fallback) failed for coordinates ({lat:.4f}, {lon:.4f})"
    logger.error(err_msg)
    raise RuntimeError(err_msg)
