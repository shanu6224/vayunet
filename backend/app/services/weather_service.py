import os
import httpx

async def get_weather(lat: float, lon: float) -> dict:
    """
    Fetches current weather and wind conditions from Open-Meteo.
    Provides wind speed, direction, temperature, humidity, surface pressure, and precipitation.
    """
    url = os.getenv("OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast")
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,relative_humidity_2m,surface_pressure,"
            "wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation"
        ),
        "hourly": "wind_speed_10m,wind_direction_10m",
        "forecast_days": 1,
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    current = data.get("current", {})
    return {
        "temperature_c": current.get("temperature_2m"),
        "humidity_pct": current.get("relative_humidity_2m"),
        "surface_pressure_hpa": current.get("surface_pressure"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wind_direction_deg": current.get("wind_direction_10m"),
        "wind_gusts_kmh": current.get("wind_gusts_10m"),
        "precipitation_mm": current.get("precipitation"),
        "source": "Open-Meteo"
    }

