import os
import time
import httpx
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .gee_service import get_pollution, GEEConfigurationError, is_gee_configured
from .weather_service import get_weather
from .risk_engine import (
    calculate_anomaly_and_risk,
    movement_from_wind,
    find_hotspot_location,
    generate_exposure_zone
)
from .places_service import get_sensitive_places

logger = logging.getLogger("vayunet.analysis")

# In-memory alert cooldown cache: {(rounded_lat, rounded_lon): (last_alert_time, last_risk)}
_ALERT_CACHE: Dict[tuple, tuple] = {}
COOLDOWN_SECONDS = 900  # 15 minutes cooldown

def _check_alert_cooldown(lat: float, lon: float, risk_level: str) -> bool:
    if risk_level not in ("MODERATE", "HIGH", "CRITICAL"):
        return False
    key = (round(lat, 2), round(lon, 2))
    now = time.time()
    if key in _ALERT_CACHE:
        last_time, last_risk = _ALERT_CACHE[key]
        if last_risk == risk_level and (now - last_time) < COOLDOWN_SECONDS:
            return False
    _ALERT_CACHE[key] = (now, risk_level)
    return True

def _get_bilingual_status(risk_level: str, user_affected: bool, hotspot_detected: bool) -> Dict[str, Any]:
    if hotspot_detected and user_affected:
        return {
            "title_en": "ATTENTION",
            "title_ta": "கவனமாக இருக்கவும்",
            "badge_color": "#EF4444",
            "summary_en": "A nearby pollution hotspot is currently aligned with the prevailing wind toward your area. Consider checking the affected-area map.",
            "summary_ta": "அருகில் உள்ள காற்று மாசு மையம், தற்போதைய காற்று வீசும் திசையால் உங்கள் பகுதியை நோக்கி நகர வாய்ப்புள்ளது. வரைபடத்தை பார்க்கவும்.",
            "action_en": "Stay indoors if possible and follow local official advisories.",
            "action_ta": "முடிந்தவரை வீட்டிற்குள் இருக்கவும், அரசு வழிகாட்டுதல்களைப் பின்பற்றவும்."
        }
    elif hotspot_detected and not user_affected:
        return {
            "title_en": "POLLUTION NEARBY",
            "title_ta": "அருகில் காற்று மாசு உள்ளது",
            "badge_color": "#F59E0B",
            "summary_en": "A pollution hotspot was detected nearby. Current wind does not indicate movement toward your area.",
            "summary_ta": "அருகில் காற்று மாசு கண்டறியப்பட்டுள்ளது. தற்போதைய காற்று உங்கள் பகுதியை நோக்கி வீசவில்லை.",
            "action_en": "Air in your immediate area is safe. Monitor for wind direction changes.",
            "action_ta": "உங்கள் பகுதியில் காற்று தற்போது பாதுகாப்பாக உள்ளது. நிலவரத்தை கவனிக்கவும்."
        }
    elif risk_level == "MODERATE":
        return {
            "title_en": "BE CAREFUL",
            "title_ta": "கவனமாக இருக்கவும்",
            "badge_color": "#F59E0B",
            "summary_en": "Pollution is slightly elevated near your area.",
            "summary_ta": "உங்கள் பகுதியில் காற்று மாசு சற்று அதிகரித்துள்ளது.",
            "action_en": "Air quality is declining. Sensitive persons should limit prolonged outdoor exertion.",
            "action_ta": "காற்று தரம் குறைகிறது. சுவாசப் பிரச்சனை உள்ளவர்கள் கவனமாக இருக்கவும்."
        }
    else:
        return {
            "title_en": "AIR IS GOOD",
            "title_ta": "காற்று சுத்தமாக உள்ளது",
            "badge_color": "#10B981",
            "summary_en": "No significant nearby pollution hotspot detected.",
            "summary_ta": "அருகில் குறிப்பிடத்தக்க காற்று மாசு மையம் எதுவும் இல்லை.",
            "action_en": "Air is safe for normal outdoor activities.",
            "action_ta": "வெளிப்புற நடவடிக்கைகளுக்கு காற்று பாதுகாப்பாக உள்ளது."
        }

async def get_human_location_name(lat: float, lon: float) -> Dict[str, str]:
    """Provides a human-readable town/city name using OSM Nominatim."""
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        headers = {"User-Agent": "VayuNet-CleanAir-Intelligence/1.0"}
        params = {"lat": lat, "lon": lon, "format": "json", "zoom": 13}
        async with httpx.AsyncClient(timeout=3.5) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                addr = data.get("address", {})
                city = (
                    addr.get("city") or addr.get("town") or
                    addr.get("suburb") or addr.get("village") or
                    addr.get("county") or "Local Area"
                )
                state = addr.get("state", "")
                name = f"{city}, {state}".strip(", ")
                return {"display_name": name, "city": city}
    except Exception as e:
        logger.debug(f"Reverse geocode fallback: {e}")
    return {"display_name": f"{lat:.3f}°N, {lon:.3f}°E", "city": "Nearby Area"}

async def analyze_location(lat: float, lon: float, demo_override: Optional[bool] = None) -> Dict[str, Any]:
    """
    Main analysis orchestrator:
    1. Fetches real Open-Meteo weather (wind, temp, humidity, pressure).
    2. Queries GEE Sentinel-5P in configurable analysis radius around user location.
    3. Finds distinct pollution hotspot vs user location.
    4. Generates downwind exposure corridor from hotspot.
    5. Formulates simple, bilingual messages (English & Tamil).
    """
    demo_flag = demo_override if demo_override is not None else (os.getenv("VAYUNET_DEMO_MODE", "false").lower() == "true")
    radius_km = float(os.getenv("ANALYSIS_RADIUS_KM", "15"))

    # 1. Fetch real weather data
    weather_data = None
    weather_err = None
    try:
        weather_data = await get_weather(lat, lon)
    except Exception as exc:
        weather_err = str(exc)
        logger.warning(f"Open-Meteo weather fetch error: {exc}")
        weather_data = {
            "temperature_c": None,
            "humidity_pct": None,
            "wind_speed_kmh": None,
            "wind_direction_deg": None,
            "wind_gusts_kmh": None,
            "precipitation_mm": 0.0,
            "source": "Weather data unavailable"
        }

    # 2. Sentinel-5P Satellite query
    pollution_data = None
    satellite_available = False
    satellite_notice = "Satellite data is temporarily unavailable."
    gee_config_msg = None

    if demo_flag:
        pollution_data = {
            "no2": 0.000155,
            "no2_max": 0.000195,
            "no2_observations": 9,
            "no2_latest": datetime.now(timezone.utc).isoformat(),
            "so2": 0.000068,
            "so2_max": 0.000098,
            "so2_observations": 7,
            "so2_latest": datetime.now(timezone.utc).isoformat(),
            "max_location": None,
            "source": "DEMO SATELLITE MODE (Testing)",
            "scientific_note": "Demo satellite proxy; configure GEE for live Sentinel-5P."
        }
        satellite_available = True
        satellite_notice = "DEMO MODE (Testing)"
    else:
        lookback = int(os.getenv("GEE_LOOKBACK_DAYS", "7"))
        try:
            pollution_data = get_pollution(lat, lon, lookback)
            satellite_available = (pollution_data["no2_observations"] > 0 or pollution_data["so2_observations"] > 0)
            if satellite_available:
                satellite_notice = "Live Sentinel-5P satellite data active"
            else:
                satellite_notice = "No recent cloud-free satellite observations in this area; weather analysis is active."
        except GEEConfigurationError as gerr:
            gee_config_msg = str(gerr)
            pollution_data = {
                "no2": None,
                "no2_max": None,
                "no2_observations": 0,
                "no2_latest": None,
                "so2": None,
                "so2_max": None,
                "so2_observations": 0,
                "so2_latest": None,
                "max_location": None,
                "source": "Satellite data is temporarily unavailable",
                "scientific_note": "GEE credentials not yet configured."
            }
        except Exception as exc:
            gee_config_msg = f"Earth Engine error: {exc}"
            pollution_data = {
                "no2": None,
                "no2_max": None,
                "no2_observations": 0,
                "no2_latest": None,
                "so2": None,
                "so2_max": None,
                "so2_observations": 0,
                "so2_latest": None,
                "max_location": None,
                "source": "Satellite data is temporarily unavailable",
                "scientific_note": str(exc)
            }

    # 3. Anomaly & Risk calculation
    risk_info = calculate_anomaly_and_risk(
        pollution_data.get("no2"),
        pollution_data.get("so2"),
        weather_data.get("wind_speed_kmh"),
        weather_data.get("humidity_pct")
    )
    risk_level = risk_info["level"]

    # 4. Movement vector from wind
    movement = movement_from_wind(
        weather_data.get("wind_speed_kmh"),
        weather_data.get("wind_direction_deg"),
        risk_level
    )

    # 5. Distinct Hotspot Location (separate from User Location)
    hotspot = find_hotspot_location(
        lat, lon,
        weather_data.get("wind_direction_deg"),
        risk_level,
        gee_max_loc=pollution_data.get("max_location"),
        is_demo=demo_flag
    )

    # 6. Potential Downwind Exposure Corridor (starts at Hotspot)
    exposure = generate_exposure_zone(
        hotspot.get("latitude"),
        hotspot.get("longitude"),
        lat, lon,
        weather_data.get("wind_speed_kmh"),
        weather_data.get("wind_direction_deg"),
        risk_level
    )

    # 7. Sensitive sites in exposure corridor
    sensitive_places = await get_sensitive_places(
        exposure["center_latitude"] if exposure else lat,
        exposure["center_longitude"] if exposure else lon
    )

    # 8. Human-readable location name
    location_info = await get_human_location_name(lat, lon)

    # 9. Simple Bilingual Status & Advice based on scenarios
    user_affected = exposure.get("user_potentially_affected", False) if exposure else False
    hotspot_detected = hotspot.get("detected", False)
    status_card = _get_bilingual_status(risk_level, user_affected, hotspot_detected)

    # Generate simple "Why this alert?" explanation
    wind_sp = weather_data.get("wind_speed_kmh")
    wind_str = f" at {wind_sp:.0f} km/h" if wind_sp is not None else ""
    wind_ta_str = f" மணிக்கு {wind_sp:.0f} கி.மீ வேகத்தில்" if wind_sp is not None else ""
    dir_en = movement.get("direction", "downwind")
    dir_ta = movement.get("direction_ta", "திசையில்")

    if hotspot_detected:
        if user_affected:
            why_en = f"A nearby pollution hotspot was detected based on satellite observations, and prevailing wind{wind_str} may move air toward your area ({dir_en})."
            why_ta = f"செயற்கைக்கோள் கண்காணிப்பில் அருகில் காற்று மாசு கண்டறியப்பட்டுள்ளது. காற்று{wind_ta_str} உங்கள் பகுதியை நோக்கி ({dir_ta}) நகர வாய்ப்புள்ளது."
        else:
            why_en = f"A pollution hotspot was detected nearby based on satellite observations. Current wind{wind_str} is blowing toward {dir_en}, away from your area."
            why_ta = f"செயற்கைக்கோள் கண்காணிப்பில் அருகில் காற்று மாசு உள்ளது. காற்று{wind_ta_str} {dir_ta} நோக்கி வீசுகிறது (உங்கள் பகுதியிலிருந்து விலகிச் செல்கிறது)."
    elif risk_level == "MODERATE":
        why_en = f"Local atmospheric observations show slight elevation above baseline with wind{wind_str} toward {dir_en}."
        why_ta = f"வழக்கமான அளவை விட காற்று மாசு சற்று உயர்ந்துள்ளது. காற்று{wind_ta_str} {dir_ta} நோக்கி வீசுகிறது."
    else:
        why_en = f"No significant nearby pollution hotspot detected based on satellite observations and current wind conditions."
        why_ta = f"செயற்கைக்கோள் கண்காணிப்பு மற்றும் தற்போதைய காற்றின் அடிப்படையில் உங்கள் பகுதியில் குறிப்பிடத்தக்க காற்று மாசு மையம் எதுவும் இல்லை."

    status_card["why_en"] = why_en
    status_card["why_ta"] = why_ta

    # 10. Alert cooldown check
    should_alert = (hotspot_detected and user_affected) or risk_level in ("HIGH", "CRITICAL")
    alert_allowed = _check_alert_cooldown(lat, lon, risk_level) if should_alert else False

    user_loc_dict = {
        "latitude": lat,
        "longitude": lon,
        "place_name": location_info["display_name"],
        "city": location_info["city"]
    }

    hotspot_dict = {
        "latitude": hotspot.get("latitude"),
        "longitude": hotspot.get("longitude"),
        "distance_km": hotspot.get("distance_km"),
        "distance_from_user_km": hotspot.get("distance_km"),
        "severity": risk_level,
        "bearing_from_user": hotspot.get("bearing_from_user"),
        "pollutant": hotspot.get("pollutant", "NO2"),
        "detected": hotspot.get("detected", False),
        "name_en": hotspot.get("name_en"),
        "name_ta": hotspot.get("name_ta"),
        "source": hotspot.get("source")
    }

    final_status = "HIGH" if (hotspot_detected and user_affected) else ("MODERATE" if hotspot_detected else risk_level)

    return {
        "status": final_status,
        "risk_level": final_status,
        "headline": status_card["title_en"],
        "user_location": user_loc_dict,
        "pollution_hotspot": hotspot_dict,
        "location": user_loc_dict,
        "hotspot": hotspot_dict,
        "analysis_radius_km": radius_km,
        "status_card": status_card,
        "risk_score": risk_info["score"],
        "risk": risk_info,
        "movement": movement,
        "exposure": exposure,
        "potential_exposure": exposure,
        "sensitive_places": sensitive_places,
        "weather": weather_data,
        "pollution": pollution_data,
        "satellite_available": satellite_available,
        "satellite_notice": satellite_notice,
        "mode": "demo" if demo_flag else "real",
        "why_this_alert": {
            "en": why_en,
            "ta": why_ta
        },
        "intelligence": {
            "summary": status_card["summary_en"],
            "recommendations": status_card["action_en"]
        },
        "alert": {
            "should_alert": should_alert and alert_allowed,
            "sound": should_alert,
            "vibrate": should_alert,
            "title_en": f"⚠️ VayuNet Alert: {status_card['title_en']}",
            "title_ta": f"⚠️ வாயுநெட் எச்சரிக்கை: {status_card['title_ta']}",
            "message_en": f"{status_card['summary_en']} Possible movement toward {dir_en}.",
            "message_ta": f"{status_card['summary_ta']} மாசு செல்லக்கூடிய திசை: {dir_ta}."
        },
        "technical_details": {
            "analysis_radius_km": radius_km,
            "no2_raw": pollution_data.get("no2"),
            "so2_raw": pollution_data.get("so2"),
            "no2_observations": pollution_data.get("no2_observations", 0),
            "so2_observations": pollution_data.get("so2_observations", 0),
            "wind_speed_kmh": weather_data.get("wind_speed_kmh"),
            "wind_direction_deg": weather_data.get("wind_direction_deg"),
            "temperature_c": weather_data.get("temperature_c"),
            "humidity_pct": weather_data.get("humidity_pct"),
            "satellite_observation_time": pollution_data.get("no2_latest") or pollution_data.get("so2_latest"),
            "anomaly_score": risk_info["score"],
            "data_source": pollution_data.get("source", "Sentinel-5P / Open-Meteo"),
            "gee_diagnostic": gee_config_msg,
            "weather_diagnostic": weather_err,
            "user_coordinates": f"{lat:.5f}, {lon:.5f}"
        },
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


