import sys
import asyncio
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.weather_service import get_weather
from app.services.risk_engine import movement_from_wind, generate_exposure_zone

lat = 9.9060
lon = 78.1402

# 1. Direct Open-Meteo API query
url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": lat,
    "longitude": lon,
    "current": "temperature_2m,relative_humidity_2m,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation",
    "timezone": "auto"
}
headers = {"User-Agent": "VayuNet-Atmospheric-Monitor/1.1 (https://github.com/shanu6224/vayunet; contact@vayunet.app)"}

with httpx.Client(timeout=10, headers=headers) as client:
    resp = client.get(url, params=params)
    status_code = resp.status_code
    current_data = resp.json().get("current", {})

# 2. Weather service parsing
weather = asyncio.run(get_weather(lat, lon))

# 3. Risk engine possible movement and exposure calculation
movement = movement_from_wind(weather["wind_speed_kmh"], weather["wind_direction_deg"], "HIGH")
hotspot_lat = lat + 0.03
hotspot_lon = lon + 0.03
exposure = generate_exposure_zone(hotspot_lat, hotspot_lon, lat, lon, weather["wind_speed_kmh"], weather["wind_direction_deg"], "HIGH")

works = movement["detected"] is True and exposure["downwind_available"] is True

print("=== DIRECT TEST VERIFICATION ===")
print(f"1. Open-Meteo response status: {status_code}")
print(f"2. wind speed: {weather['wind_speed_kmh']} km/h")
print(f"3. wind direction: {weather['wind_direction_deg']}°")
print(f"4. whether possible movement calculation now works: {works} (Movement bearing: {movement['bearing_deg']}°, Direction: {movement['direction']} / {movement['direction_short']}, Plume distance: {exposure['distance_km']} km)")
