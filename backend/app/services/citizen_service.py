import os
import math
import uuid
import base64
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger("vayunet.citizen")

# Category labels (English & Tamil)
CATEGORY_LABELS = {
    "smoke_haze": {
        "en": "Smoke / Heavy Haze",
        "ta": "புகை / அடர் மூடுபனி",
        "icon": "🌫️"
    },
    "agricultural_fire": {
        "en": "Agricultural / Waste Fire",
        "ta": "விவசாய / குப்பை எரிப்பு",
        "icon": "🔥"
    },
    "industrial_emission": {
        "en": "Industrial / Factory Plume",
        "ta": "தொழிற்சாலை புகை",
        "icon": "🏭"
    },
    "dust": {
        "en": "Dust / Construction Plume",
        "ta": "புழுதி / கட்டுமான தூசு",
        "icon": "💨"
    },
    "other": {
        "en": "Other Visible Pollution",
        "ta": "மற்றவை",
        "icon": "⚠️"
    }
}

# In-memory prototype observation storage
_OBSERVATIONS: List[Dict[str, Any]] = []

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance formula between two GPS coordinates in kilometers."""
    R = 6371.0  # Earth's mean radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)

def generate_deterministic_assessment(category: str, description: str) -> Dict[str, Any]:
    """
    Scientifically cautious assessment when AI vision API is offline.
    Never claims causal proof of NO2/SO2; frames evidence as localized visual indicator.
    """
    cat_info = CATEGORY_LABELS.get(category, CATEGORY_LABELS["other"])
    cat_en = cat_info["en"]
    cat_ta = cat_info["ta"]

    if category in ("smoke_haze", "agricultural_fire", "industrial_emission", "dust"):
        return {
            "has_visible_evidence": True,
            "status": "POSSIBLE_VISIBLE_EVIDENCE",
            "confidence": "MODERATE",
            "headline_en": "Possible Visible Pollution Evidence",
            "headline_ta": "சாத்தியமான நேரடி காற்று மாசு ஆதாரம்",
            "assessment_en": (
                f"Citizen photo submitted as visual evidence for {cat_en.lower()}. "
                "Atmospheric particulate or emission visible in the local frame. "
                "Requires ground verification; does not measure chemical gas concentrations (NO₂/SO₂)."
            ),
            "assessment_ta": (
                f"{cat_ta} தொடர்பான புகைப்பட ஆதாரம் பதிவு செய்யப்பட்டுள்ளது. "
                "இது கள ஆய்வுக்கு உட்பட்ட பார்வைக் கள ஆதாரமாகும்; வாயு அளவீடுகளின் ஆதாரம் அல்ல."
            ),
            "verification_recommendation": "Priority ground verification recommended alongside satellite columns.",
            "source": "VayuNet Deterministic Citizen Assessment",
            "disclaimer": "Citizen photos provide qualitative visible context and ground-level alerts. They do not quantify gas column densities."
        }
    else:
        return {
            "has_visible_evidence": True,
            "status": "UNVERIFIED_CITIZEN_REPORT",
            "confidence": "REQUIRES_VERIFICATION",
            "headline_en": "Citizen Report Awaiting Verification",
            "headline_ta": "சரிபார்க்கப்பட வேண்டிய பொதுமக்கள் பதிவு",
            "assessment_en": (
                "Citizen report submitted for general visible air quality concern. "
                "Recorded as citizen ground evidence; awaiting localized inspection."
            ),
            "assessment_ta": (
                "பொதுமக்கள் காற்று மாசு பதிவு பெறப்பட்டுள்ளது. கள சரிபார்ப்புக்கு உட்பட்டது."
            ),
            "verification_recommendation": "Awaiting localized inspection.",
            "source": "VayuNet Deterministic Citizen Assessment",
            "disclaimer": "Citizen photos provide qualitative visible context and ground-level alerts. They do not quantify gas column densities."
        }

async def assess_citizen_photo(photo_base64: str, category: str, description: str) -> Dict[str, Any]:
    """
    Assesses photo evidence using Google Gemini vision when available,
    strictly adhering to scientific caution guidelines.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    cat_info = CATEGORY_LABELS.get(category, CATEGORY_LABELS["other"])

    if not api_key:
        return generate_deterministic_assessment(category, description)

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        # Strip data URL prefix if present
        clean_b64 = photo_base64
        mime_type = "image/jpeg"
        if "," in photo_base64:
            header, clean_b64 = photo_base64.split(",", 1)
            if "png" in header:
                mime_type = "image/png"
            elif "webp" in header:
                mime_type = "image/webp"

        image_bytes = base64.b64decode(clean_b64)

        prompt = f"""
You are the scientific visual verification engine for VayuNet (Hyper-local Pollution Intelligence & Climate Resilience).
Analyze this citizen-submitted photo for VISIBLE signs of pollution (smoke, haze, fire, industrial plumes, dust).

REPORT CONTEXT:
- Category claimed by user: {cat_info['en']}
- User description: {description or 'None provided'}

CRITICAL SCIENTIFIC SAFETY RULES:
1. Treat this photo strictly as CITIZEN EVIDENCE / VISUAL OBSERVATION, NOT as scientific proof of chemical gas concentration (NO2/SO2).
2. Use cautious wording: "possible visible pollution evidence", "potential plume", "requires verification".
3. NEVER claim causation or exact gas mass from the image alone.
4. Provide response in exact JSON:
{{
  "has_visible_evidence": true,
  "status": "POSSIBLE_VISIBLE_EVIDENCE" or "INCONCLUSIVE_VISIBLE_EVIDENCE",
  "confidence": "HIGH" or "MODERATE" or "LOW",
  "headline_en": "Possible Visible Pollution Evidence",
  "headline_ta": "சாத்தியமான நேரடி காற்று மாசு ஆதாரம்",
  "assessment_en": "1-2 sentences cautious visual assessment emphasizing need for ground verification and that this does not measure gas column density",
  "assessment_ta": "Tamil translation of assessment",
  "verification_recommendation": "Brief recommendation for authorities or citizens"
}}
"""
        response = client.models.generate_content(
            model=model,
            contents=[
                genai.types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt
            ],
            config={"response_mime_type": "application/json"}
        )

        import json
        parsed = json.loads(response.text)
        return {
            "has_visible_evidence": parsed.get("has_visible_evidence", True),
            "status": parsed.get("status", "POSSIBLE_VISIBLE_EVIDENCE"),
            "confidence": parsed.get("confidence", "MODERATE"),
            "headline_en": parsed.get("headline_en", "Possible Visible Pollution Evidence"),
            "headline_ta": parsed.get("headline_ta", "சாத்தியமான நேரடி காற்று மாசு ஆதாரம்"),
            "assessment_en": parsed.get("assessment_en", "Visual evidence indicates potential atmospheric particulates. Requires verification."),
            "assessment_ta": parsed.get("assessment_ta", "காட்சிப் பதிவு சாத்தியமான காற்று மாசைக் குறிக்கிறது. கள ஆய்வு தேவை."),
            "verification_recommendation": parsed.get("verification_recommendation", "Ground verification prioritized."),
            "source": f"Gemini Vision ({model})",
            "disclaimer": "Citizen photos provide qualitative visible context and ground-level alerts. They do not quantify gas column densities."
        }
    except Exception as exc:
        logger.warning(f"Gemini vision assessment failed: {exc}. Using deterministic assessment.")
        fallback = generate_deterministic_assessment(category, description)
        fallback["source"] = "VayuNet Deterministic Assessment (Gemini vision unavailable)"
        return fallback

async def record_observation(
    latitude: float,
    longitude: float,
    photo_base64: str,
    category: str = "smoke_haze",
    description: str = ""
) -> Dict[str, Any]:
    """
    Records a new citizen pollution observation and runs the AI visual assessment.
    """
    obs_id = f"obs_{uuid.uuid4().hex[:10]}"
    cat_key = category if category in CATEGORY_LABELS else "other"
    cat_info = CATEGORY_LABELS[cat_key]

    # Conduct AI visual assessment
    ai_assessment = await assess_citizen_photo(photo_base64, cat_key, description)

    observation = {
        "id": obs_id,
        "latitude": round(latitude, 5),
        "longitude": round(longitude, 5),
        "category": cat_key,
        "category_label_en": cat_info["en"],
        "category_label_ta": cat_info["ta"],
        "category_icon": cat_info["icon"],
        "description": description.strip(),
        "photo_preview": photo_base64[:200000],  # Keep reasonable preview size in memory
        "ai_assessment": ai_assessment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verified": False,
        "evidence_type": "Citizen Qualitative Ground Evidence"
    }

    # Store in memory (most recent first)
    _OBSERVATIONS.insert(0, observation)

    # Keep memory bounded to 200 most recent observations
    if len(_OBSERVATIONS) > 200:
        _OBSERVATIONS.pop()

    return observation

def get_nearby_observations(
    latitude: float,
    longitude: float,
    radius_km: float = 15.0,
    limit: int = 15,
    include_photo: bool = True
) -> List[Dict[str, Any]]:
    """
    Retrieves citizen observations within a given radius (km) of user coordinates.
    """
    nearby = []
    for obs in _OBSERVATIONS:
        dist = calculate_distance_km(latitude, longitude, obs["latitude"], obs["longitude"])
        if dist <= radius_km:
            item = dict(obs)
            item["distance_km"] = dist
            if not include_photo:
                item.pop("photo_preview", None)
            nearby.append(item)

    # Sort by closest first, then most recent
    nearby.sort(key=lambda x: (x["distance_km"], x["timestamp"]))
    return nearby[:limit]

def get_all_observations_count() -> int:
    return len(_OBSERVATIONS)
