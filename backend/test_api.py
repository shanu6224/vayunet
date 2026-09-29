import asyncio
import os
import sys
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)

def test_endpoints():
    print("Testing GET /api/health...")
    r = client.get("/api/health")
    assert r.status_code == 200

    print("Testing GET /api/status...")
    r = client.get("/api/status")
    assert r.status_code == 200

    print("Testing GET /api/config...")
    r = client.get("/api/config")
    assert r.status_code == 200

    print("\n--- SCENARIO A: Stable conditions, no significant anomaly ---")
    os.environ["VAYUNET_DEMO_MODE"] = "false"
    r = client.post("/api/analyze", json={"latitude": 13.0827, "longitude": 80.2707})
    assert r.status_code == 200
    data = r.json()
    print("Scenario A Status:", data["status_card"]["title_en"])
    print("Hotspot Detected:", data["pollution_hotspot"]["detected"])
    print("Hotspot Name:", data["pollution_hotspot"]["name_en"])
    assert data["pollution_hotspot"]["detected"] is False
    assert data["pollution_hotspot"]["name_en"] == "No clear hotspot detected"
    assert data["status_card"]["title_en"] in ("AIR IS GOOD", "BE CAREFUL")
    assert data["user_location"]["latitude"] == 13.0827

    print("\n--- SCENARIO B & C: Demo Mode with Hotspot Separation & Downwind Check ---")
    os.environ["VAYUNET_DEMO_MODE"] = "true"
    r = client.post("/api/analyze", json={"latitude": 9.9252, "longitude": 78.1198})
    assert r.status_code == 200
    ddata = r.json()
    print("Demo Status:", ddata["status_card"]["title_en"])
    print("Demo Hotspot Detected:", ddata["pollution_hotspot"]["detected"])
    print("Demo Hotspot Coords:", ddata["pollution_hotspot"]["latitude"], ddata["pollution_hotspot"]["longitude"])
    print("User Coords:", ddata["user_location"]["latitude"], ddata["user_location"]["longitude"])
    print("Distance km:", ddata["pollution_hotspot"]["distance_km"])
    print("User in Downwind Path:", ddata["exposure"]["user_potentially_affected"])
    assert ddata["pollution_hotspot"]["detected"] is True
    # Hotspot MUST NOT equal user location
    assert (ddata["pollution_hotspot"]["latitude"], ddata["pollution_hotspot"]["longitude"]) != (9.9252, 78.1198)
    assert ddata["exposure"]["geojson"] is not None

    print("\n--- SCENARIO D: GEE unconfigured graceful fallback ---")
    os.environ["VAYUNET_DEMO_MODE"] = "false"
    r = client.post("/api/analyze", json={"latitude": 11.606, "longitude": 79.749})
    assert r.status_code == 200
    gdata = r.json()
    print("Satellite notice:", gdata["satellite_notice"])
    assert "temporarily unavailable" in gdata["satellite_notice"].lower()
    # Main UI should not expose raw GEE_PROJECT_ID
    assert "GEE_PROJECT_ID" not in gdata["status_card"]["title_en"]
    assert "GEE_PROJECT_ID" not in gdata["status_card"]["summary_en"]
    # Technical details houses the diagnostic
    assert "GEE_PROJECT_ID" in gdata["technical_details"]["gee_diagnostic"]

    print("\nAll scenario unit tests passed successfully!")

if __name__ == "__main__":
    test_endpoints()

