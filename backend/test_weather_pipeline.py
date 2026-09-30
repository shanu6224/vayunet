import asyncio
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app
from app.services.weather_service import get_weather
from app.services.risk_engine import movement_from_wind, generate_exposure_zone
from app.services.analysis import analyze_location, _get_bilingual_status

def test_weather_pipeline():
    test_lat = 9.9060
    test_lon = 78.1402
    print(f"\n==================================================")
    print(f"1. TESTING WEATHER FETCH FOR ({test_lat}, {test_lon})")
    print(f"==================================================")
    weather = asyncio.run(get_weather(test_lat, test_lon))
    print("Weather retrieved successfully:")
    for k, v in weather.items():
        print(f"  {k}: {v}")

    # Check required fields
    assert weather.get("temperature_c") is not None, "Missing temperature_c"
    assert weather.get("humidity_pct") is not None, "Missing humidity_pct"
    assert weather.get("wind_speed_kmh") is not None, "Missing wind_speed_kmh"
    assert weather.get("wind_direction_deg") is not None, "Missing wind_direction_deg"
    print("[OK] All required weather fields verified!")

    print(f"\n==================================================")
    print(f"2. TESTING RISK ENGINE MOVEMENT & EXPOSURE CORRIDOR")
    print(f"==================================================")
    # Movement calculation
    movement = movement_from_wind(weather["wind_speed_kmh"], weather["wind_direction_deg"], "HIGH")
    print(f"Movement detected: {movement['detected']}")
    print(f"Movement direction: {movement['direction']} ({movement['direction_short']})")
    print(f"Bearing deg: {movement['bearing_deg']}°")
    print(f"Text EN: {movement['text_en']}")
    assert movement["detected"] is True
    assert movement["bearing_deg"] is not None

    # Exposure corridor calculation from hotspot
    hotspot_lat = test_lat + 0.03
    hotspot_lon = test_lon + 0.03
    exposure = generate_exposure_zone(
        hotspot_lat, hotspot_lon,
        test_lat, test_lon,
        weather["wind_speed_kmh"],
        weather["wind_direction_deg"],
        "HIGH"
    )
    print(f"Exposure corridor generated:")
    print(f"  Downwind available: {exposure['downwind_available']}")
    print(f"  Distance km: {exposure['distance_km']}")
    print(f"  Bearing deg: {exposure['bearing_deg']} deg")
    print(f"  User potentially affected: {exposure['user_potentially_affected']}")
    assert exposure["downwind_available"] is True
    assert exposure["corridor_geojson"] is not None
    assert exposure["affected_geojson"] is not None
    print("[OK] Movement and exposure calculations verified!")

    print(f"\n==================================================")
    print(f"3. TESTING FULL LOCAL /api/analyze ENDPOINT")
    print(f"==================================================")
    client = TestClient(app)
    resp = client.post("/api/analyze", json={"latitude": test_lat, "longitude": test_lon})
    assert resp.status_code == 200, f"Error {resp.status_code}: {resp.text}"
    data = resp.json()
    print("Analyze response status:", data.get("status"))
    print("Analyze response headline:", data.get("headline"))
    print("Weather in analyze:", data.get("weather"))
    print("Movement in analyze:", data.get("movement"))
    print("Exposure in analyze downwind_available:", data.get("exposure", {}).get("downwind_available"))
    assert data["weather"]["wind_speed_kmh"] is not None
    assert data["weather"]["wind_direction_deg"] is not None
    assert data["movement"]["detected"] is True
    print("[OK] Local /api/analyze pipeline verified!")

    print(f"\n==================================================")
    print(f"4. TESTING UI SAFETY WHEN WIND IS UNAVAILABLE")
    print(f"==================================================")
    # Simulate analyze_location with dummy coordinates in a test harness where wind is None
    unavail_movement = movement_from_wind(None, None, "HIGH")
    print("Unavail movement text:", unavail_movement["text_en"])
    assert "Wind data is currently unavailable" in unavail_movement["text_en"]
    assert unavail_movement["detected"] is False

    unavail_exposure = generate_exposure_zone(hotspot_lat, hotspot_lon, test_lat, test_lon, None, None, "HIGH")
    print("Unavail exposure downwind_available:", unavail_exposure["downwind_available"])
    print("Unavail exposure text:", unavail_exposure["text_en"])
    assert unavail_exposure["downwind_available"] is False
    assert "Wind data is currently unavailable" in unavail_exposure["text_en"]

    safety_card = _get_bilingual_status("HIGH", False, True, wind_available=False)
    print("Safety card title:", safety_card["title_en"])
    print("Safety card summary:", safety_card["summary_en"])
    print("Safety card action:", safety_card["action_en"])
    # MUST NOT show "Air in your immediate area is safe" or "not currently in downwind path"
    assert "Air in your immediate area is safe" not in safety_card["action_en"]
    assert "not currently" not in safety_card["summary_en"]
    assert "Wind data is currently unavailable" in safety_card["action_en"]
    print("[OK] UI safety fix verified: safe assumptions completely blocked when wind is unavailable!")

    print("\n==================================================")
    print("ALL WEATHER PIPELINE & SAFETY TESTS PASSED! (Code 0)")
    print("==================================================")

if __name__ == "__main__":
    test_weather_pipeline()
