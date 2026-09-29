import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("vayunet.gemini")

def generate_algorithmic_explanation(
    risk_level: str,
    score: float,
    movement_dir: Optional[str],
    bearing: Optional[float],
    wind_speed: Optional[float],
    primary_driver: str,
    places_count: int
) -> Dict[str, str]:
    """Fallback scientific explanation when Gemini API is not configured."""
    if risk_level == "CRITICAL":
        summary = (
            f"Severe atmospheric {primary_driver} column anomaly detected (composite risk {score:.2f}). "
            f"Stagnation and wind conditions indicate elevated potential exposure."
        )
        recommendations = "Sensitive groups should limit outdoor exertion. Authorities should prioritize ground verification."
        why_flagged = f"Atmospheric column density of {primary_driver} significantly exceeds regional baseline."
    elif risk_level == "HIGH":
        summary = (
            f"Elevated {primary_driver} pollution anomaly signal detected (risk {score:.2f}). "
            f"Possible advection moving toward {movement_dir or 'downwind'} (~{bearing or 0}°)."
        )
        recommendations = "Close windows if downwind of industrial or heavy traffic corridors. Check official local advisories."
        why_flagged = f"{primary_driver} levels and wind transport vector suggest increased downwind exposure."
    elif risk_level == "MODERATE":
        summary = (
            f"Moderate pollution signal identified. Wind speed of {wind_speed or 0} km/h "
            f"is actively transporting atmospheric particles toward {movement_dir or 'downwind'}."
        )
        recommendations = "Standard conditions for most individuals. Continue routine monitoring."
        why_flagged = "Slightly elevated column density within normal operational fluctuation."
    else:
        summary = "Atmospheric column concentrations are near clean baseline values. No significant anomaly detected."
        recommendations = "Air quality proxy is currently stable. Good for general outdoor activities."
        why_flagged = "Pollutant observations are within clean baseline thresholds."

    return {
        "summary": summary,
        "recommendations": recommendations,
        "why_flagged": why_flagged,
        "source": "VayuNet Deterministic Decision Support"
    }

async def explain_pollution_risk(
    risk_data: Dict[str, Any],
    weather_data: Dict[str, Any],
    movement_data: Dict[str, Any],
    places: list
) -> Dict[str, str]:
    """
    Provides human-readable explainability for the detected conditions.
    Uses Gemini when GEMINI_API_KEY is available; falls back to deterministic decision logic.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    risk_level = risk_data.get("level", "LOW")
    score = risk_data.get("score", 0.0)
    movement_dir = movement_data.get("direction")
    bearing = movement_data.get("bearing_deg")
    wind_speed = weather_data.get("wind_speed_kmh")
    primary_driver = risk_data.get("primary_driver", "pollutants")

    if not api_key:
        return generate_algorithmic_explanation(
            risk_level, score, movement_dir, bearing, wind_speed, primary_driver, len(places)
        )

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        prompt = f"""
You are the scientific decision-support intelligence for VayuNet (Hyper-local Pollution Intelligence & Climate Resilience).
Explain the following atmospheric observation for decision makers and local citizens.
Use precise, scientifically responsible language: say 'possible movement' and 'potential exposure', NEVER claim exact ground plume certainty.

OBSERVATIONS:
- Risk Level: {risk_level} (Score: {score})
- Primary Driver: {primary_driver}
- Weather: Temp {weather_data.get('temperature_c')}C, Wind {wind_speed} km/h from {weather_data.get('wind_direction_deg')} deg
- Possible Movement: Toward {movement_dir} (bearing {bearing} deg)
- Sensitive places identified downwind: {len(places)}

Provide your response in exactly this JSON format:
{{
  "summary": "1-2 sentence concise overview of current atmospheric signal and potential movement",
  "recommendations": "1-2 practical human actions or verification priorities",
  "why_flagged": "Scientific reason why this risk level was assigned"
}}
"""
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )
        import json
        parsed = json.loads(response.text)
        return {
            "summary": parsed.get("summary", ""),
            "recommendations": parsed.get("recommendations", ""),
            "why_flagged": parsed.get("why_flagged", ""),
            "source": f"Gemini AI ({model})"
        }
    except Exception as exc:
        logger.warning(f"Gemini explanation generation failed: {exc}. Using deterministic fallback.")
        fallback = generate_algorithmic_explanation(
            risk_level, score, movement_dir, bearing, wind_speed, primary_driver, len(places)
        )
        fallback["source"] = "VayuNet Deterministic Fallback (Gemini unavailable)"
        return fallback
