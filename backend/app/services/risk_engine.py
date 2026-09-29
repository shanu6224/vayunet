import math
from typing import Dict, Any, Optional, Tuple, List

# Normalization baselines for Sentinel-5P column density (mol/m^2)
NO2_CLEAN_BASELINE = 0.00003
NO2_ELEVATED = 0.00010
NO2_HIGH = 0.00018
NO2_CRITICAL = 0.00030

SO2_CLEAN_BASELINE = 0.00001
SO2_ELEVATED = 0.00006
SO2_HIGH = 0.00015
SO2_CRITICAL = 0.00025

def _normalize_piecewise(val: Optional[float], clean: float, elevated: float, high: float, critical: float) -> Optional[float]:
    if val is None:
        return None
    if val <= clean:
        return max(0.0, val / clean * 0.25)
    if val <= elevated:
        return 0.25 + 0.25 * ((val - clean) / (elevated - clean))
    if val <= high:
        return 0.50 + 0.25 * ((val - elevated) / (high - elevated))
    return min(1.0, 0.75 + 0.25 * ((val - high) / max(0.00001, (critical - high))))

def calculate_anomaly_and_risk(
    no2: Optional[float],
    so2: Optional[float],
    wind_speed_kmh: Optional[float],
    humidity_pct: Optional[float] = None
) -> Dict[str, Any]:
    """
    Computes an explainable multi-factor pollution anomaly score and classifies risk:
    LOW, MODERATE, HIGH, CRITICAL.
    """
    no2_score = _normalize_piecewise(no2, NO2_CLEAN_BASELINE, NO2_ELEVATED, NO2_HIGH, NO2_CRITICAL)
    so2_score = _normalize_piecewise(so2, SO2_CLEAN_BASELINE, SO2_ELEVATED, SO2_HIGH, SO2_CRITICAL)

    available_scores = [s for s in (no2_score, so2_score) if s is not None]
    if not available_scores:
        # Fallback to meteorological stagnation risk if satellite observations are temporarily unavailable
        weather_risk = "LOW"
        base_score = 0.15
        if wind_speed_kmh is not None and wind_speed_kmh < 4.0:
            weather_risk = "MODERATE"
            base_score = 0.40
        return {
            "level": weather_risk,
            "score": base_score,
            "no2_score": None,
            "so2_score": None,
            "weather_modifier": 0.0,
            "baseline_limited": True,
            "primary_driver": "Weather Stagnation Proxy" if weather_risk == "MODERATE" else "Atmospheric Baseline",
            "explanation": "Satellite data temporarily unavailable; weather analysis is active."
        }

    satellite_base = max(available_scores)

    weather_mod = 0.0
    if wind_speed_kmh is not None:
        if wind_speed_kmh < 5.0:
            weather_mod += 0.08  # Stagnation traps pollutants
        elif wind_speed_kmh < 10.0:
            weather_mod += 0.04
        elif wind_speed_kmh > 35.0:
            weather_mod -= 0.05  # Dispersion reduces column density
    
    if humidity_pct is not None and humidity_pct > 80:
        weather_mod += 0.03

    final_score = max(0.0, min(1.0, satellite_base + weather_mod))

    if final_score >= 0.80:
        level = "CRITICAL"
    elif final_score >= 0.58:
        level = "HIGH"
    elif final_score >= 0.35:
        level = "MODERATE"
    else:
        level = "LOW"

    return {
        "level": level,
        "score": round(final_score, 3),
        "no2_score": round(no2_score, 3) if no2_score is not None else None,
        "so2_score": round(so2_score, 3) if so2_score is not None else None,
        "weather_modifier": round(weather_mod, 3),
        "baseline_limited": False,
        "primary_driver": "NO2" if (no2_score or 0) >= (so2_score or 0) else "SO2"
    }

def movement_from_wind(wind_speed_kmh: Optional[float], wind_direction_deg: Optional[float], risk_level: str) -> Dict[str, Any]:
    """
    Computes possible pollution movement from meteorological wind.
    Meteorological wind comes FROM wind_direction_deg; advection moves (+180 deg).
    """
    if wind_direction_deg is None:
        return {
            "detected": False,
            "direction": "Unknown",
            "direction_short": "—",
            "direction_ta": "தெரியவில்லை",
            "bearing_deg": None,
            "confidence": 0.0,
            "text_en": "Wind direction unavailable",
            "text_ta": "காற்றின் திசை கிடைக்கவில்லை"
        }

    bearing = (wind_direction_deg + 180.0) % 360.0
    labels = ["North", "North-East", "East", "South-East", "South", "South-West", "West", "North-West"]
    labels_short = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    labels_ta = ["வடக்கு", "வடகிழக்கு", "கிழக்கு", "தென்கிழக்கு", "தெற்கு", "தென்மேற்கு", "மேற்கு", "வடமேற்கு"]

    idx = int((bearing + 22.5) // 45) % 8
    label_en = labels[idx]
    label_short = labels_short[idx]
    label_ta = labels_ta[idx]

    confidence = 0.40
    if wind_speed_kmh is not None:
        confidence = min(0.92, 0.40 + (wind_speed_kmh / 40.0) * 0.50)

    is_elevated = risk_level in ("MODERATE", "HIGH", "CRITICAL")
    text_en = f"Possible pollution movement toward: {label_en} ({label_short})" if is_elevated else f"Wind blowing toward: {label_en} ({label_short})"
    text_ta = f"மாசு செல்லக்கூடிய திசை: {label_ta}" if is_elevated else f"காற்று வீசும் திசை: {label_ta}"

    return {
        "detected": True,
        "direction": label_en,
        "direction_short": label_short,
        "direction_ta": label_ta,
        "bearing_deg": round(bearing, 1),
        "confidence": round(confidence, 2),
        "text_en": text_en,
        "text_ta": text_ta
    }

def _destination_point(lat: float, lon: float, distance_km: float, bearing_deg: float) -> Tuple[float, float]:
    """Calculates destination coordinates given start point, distance in km, and bearing."""
    R = 6371.0
    lat_r = math.radians(lat)
    lon_r = math.radians(lon)
    brg_r = math.radians(bearing_deg)

    d_div_r = distance_km / R
    dest_lat = math.asin(
        math.sin(lat_r) * math.cos(d_div_r) +
        math.cos(lat_r) * math.sin(d_div_r) * math.cos(brg_r)
    )
    dest_lon = lon_r + math.atan2(
        math.sin(brg_r) * math.sin(d_div_r) * math.cos(lat_r),
        math.cos(d_div_r) - math.sin(lat_r) * math.sin(dest_lat)
    )
    return math.degrees(dest_lat), math.degrees(dest_lon)

def find_hotspot_location(
    user_lat: float,
    user_lon: float,
    wind_direction_deg: Optional[float],
    risk_level: str,
    gee_max_loc: Optional[Dict[str, float]] = None,
    is_demo: bool = False
) -> Dict[str, Any]:
    """
    Identifies the pollution hotspot location separate from the user location.
    The user's location is where the user is; the hotspot is where the pollution anomaly originates.
    If real GEE max pixel location is provided and elevated, uses that location.
    If in demo mode, provides a clear simulated hotspot in the surrounding area for testing.
    If data does NOT support identifying a separate hotspot, says: 'No clear hotspot detected'.
    """
    labels = ["North", "North-East", "East", "South-East", "South", "South-West", "West", "North-West"]
    labels_ta = ["வடக்கு", "வடகிழக்கு", "கிழக்கு", "தென்கிழக்கு", "தெற்கு", "தென்மேற்கு", "மேற்கு", "வடமேற்கு"]

    # 1. Use real GEE maximum concentration pixel if available
    if gee_max_loc and gee_max_loc.get("latitude") is not None and gee_max_loc.get("longitude") is not None:
        g_lat = float(gee_max_loc["latitude"])
        g_lon = float(gee_max_loc["longitude"])
        dist = math.hypot((g_lat - user_lat) * 111.0, (g_lon - user_lon) * 111.0 * math.cos(math.radians(user_lat)))
        if dist >= 0.5:
            brg = (math.degrees(math.atan2(g_lon - user_lon, g_lat - user_lat)) + 360.0) % 360.0
            idx = int((brg + 22.5) // 45) % 8
            return {
                "latitude": round(g_lat, 5),
                "longitude": round(g_lon, 5),
                "detected": True,
                "pollutant": "NO2",
                "name_en": f"Pollution hotspot (~{dist:.1f} km {labels[idx]})",
                "name_ta": f"மாசு மையம் (~{dist:.1f} கி.மீ {labels_ta[idx]})",
                "distance_km": round(dist, 1),
                "bearing_from_user": round(brg, 1),
                "source": "Sentinel-5P Satellite Observation"
            }

    # 2. In DEMO mode, provide a realistic nearby hotspot in the surrounding area (Area B) for evaluation
    if is_demo:
        upwind_bearing = wind_direction_deg if wind_direction_deg is not None else 45.0
        offset_dist = 4.8  # km
        hotspot_lat, hotspot_lon = _destination_point(user_lat, user_lon, offset_dist, upwind_bearing)
        idx = int((upwind_bearing + 22.5) // 45) % 8
        return {
            "latitude": round(hotspot_lat, 5),
            "longitude": round(hotspot_lon, 5),
            "detected": True,
            "pollutant": "NO2",
            "name_en": f"Pollution hotspot (~{offset_dist:.1f} km {labels[idx]})",
            "name_ta": f"மாசு மையம் (~{offset_dist:.1f} கி.மீ {labels_ta[idx]})",
            "distance_km": offset_dist,
            "bearing_from_user": round(upwind_bearing, 1),
            "source": "DEMO Simulation"
        }

    # 3. If data does not support a separate hotspot, do NOT invent one
    return {
        "latitude": None,
        "longitude": None,
        "detected": False,
        "pollutant": None,
        "name_en": "No clear hotspot detected",
        "name_ta": "குறிப்பிடத்தக்க மாசு மையம் இல்லை",
        "distance_km": None,
        "bearing_from_user": None,
        "source": "Baseline Observation"
    }

def generate_exposure_zone(
    hotspot_lat: Optional[float],
    hotspot_lon: Optional[float],
    user_lat: float,
    user_lon: float,
    wind_speed_kmh: Optional[float],
    wind_direction_deg: Optional[float],
    risk_level: str
) -> Optional[Dict[str, Any]]:
    """
    Constructs a downwind exposure corridor polygon (GeoJSON) starting from the pollution HOTSPOT
    and expanding downwind along the movement vector.
    Calculates whether the user is located in the downwind path of the hotspot.
    """
    if wind_direction_deg is None:
        return None

    # Pollution movement and exposure corridors ONLY originate from a detected pollution hotspot.
    # They NEVER originate from the user's location.
    if hotspot_lat is None or hotspot_lon is None:
        return None

    orig_lat = hotspot_lat
    orig_lon = hotspot_lon

    speed = wind_speed_kmh if wind_speed_kmh is not None else 10.0
    distance_km = max(3.0, min(25.0, speed * 0.45 + 3.0))
    downwind_bearing = (wind_direction_deg + 180.0) % 360.0
    half_angle = 26.0

    # 1. 🟠 ORANGE: Possible Pollution Movement Corridor (Starts at Hotspot, tighter dispersion)
    corridor_dist = max(2.5, distance_km * 0.65)
    half_angle_corridor = 18.0
    corridor_coords: List[List[float]] = [[orig_lon, orig_lat]]
    for i in range(7):
        ang = (downwind_bearing - half_angle_corridor) + (2 * half_angle_corridor * i / 6.0)
        plat, plon = _destination_point(orig_lat, orig_lon, corridor_dist, ang % 360.0)
        corridor_coords.append([round(plon, 5), round(plat, 5)])
    corridor_coords.append([orig_lon, orig_lat])

    # 2. 🟡 YELLOW: Potentially Affected Area (Expands further downwind with wider spread)
    half_angle_affected = 32.0
    affected_coords: List[List[float]] = [[orig_lon, orig_lat]]
    for i in range(9):
        ang = (downwind_bearing - half_angle_affected) + (2 * half_angle_affected * i / 8.0)
        plat, plon = _destination_point(orig_lat, orig_lon, distance_km, ang % 360.0)
        affected_coords.append([round(plon, 5), round(plat, 5)])
    affected_coords.append([orig_lon, orig_lat])

    corridor_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [corridor_coords]
        },
        "properties": {
            "title": "Possible Pollution Movement",
            "color": "#f97316",
            "distance_km": round(corridor_dist, 1)
        }
    }

    affected_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [affected_coords]
        },
        "properties": {
            "title": "Potentially Affected Area",
            "color": "#eab308",
            "distance_km": round(distance_km, 1)
        }
    }

    center_lat, center_lon = _destination_point(orig_lat, orig_lon, distance_km * 0.55, downwind_bearing)

    # Angular Downwind Verification:
    # Only if hotspot is distinct from user, check if wind carries pollution toward the user
    user_affected = False
    movement_toward_user = False
    if hotspot_lat is not None and hotspot_lon is not None:
        brg_h2u = (math.degrees(math.atan2(user_lon - hotspot_lon, user_lat - hotspot_lat)) + 360.0) % 360.0
        angle_diff = abs((downwind_bearing - brg_h2u + 180.0) % 360.0 - 180.0)
        user_dist = math.hypot((user_lat - hotspot_lat) * 111.0, (user_lon - hotspot_lon) * 111.0 * math.cos(math.radians(user_lat)))

        # User is in downwind cone if within 35 degrees of downwind bearing and within plume reach
        if angle_diff <= 35.0 and user_dist <= (distance_km * 1.35):
            user_affected = True
            movement_toward_user = True
    elif risk_level in ("HIGH", "CRITICAL"):
        user_affected = True

    return {
        "origin_latitude": round(orig_lat, 5),
        "origin_longitude": round(orig_lon, 5),
        "center_latitude": round(center_lat, 5),
        "center_longitude": round(center_lon, 5),
        "distance_km": round(distance_km, 1),
        "bearing_deg": round(downwind_bearing, 1),
        "user_potentially_affected": user_affected,
        "movement_toward_user": movement_toward_user,
        "corridor_geojson": corridor_geojson,
        "affected_geojson": affected_geojson,
        "geojson": affected_geojson,
        "text_en": f"Potential affected area extending ~{round(distance_km, 1)} km downwind.",
        "text_ta": f"சுமார் {round(distance_km, 1)} கி.மீ தூரம் வரை காற்று மாசு பரவ வாய்ப்புள்ளது."
    }


