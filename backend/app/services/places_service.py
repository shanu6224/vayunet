import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger("vayunet.places")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

async def get_sensitive_places(lat: float, lon: float, radius_m: int = 4000) -> List[Dict[str, Any]]:
    """
    Finds nearby potentially sensitive sites (schools, hospitals, clinics, residential suburbs)
    near the potential exposure corridor.
    Completely optional: fails silently and returns empty list if external OSM service is unreachable.
    """
    # Overpass QL query around coordinates
    query = f"""
    [out:json][timeout:4];
    (
      node["amenity"~"hospital|school|clinic"](around:{radius_m},{lat},{lon});
      node["place"~"suburb|town|village"](around:{radius_m},{lat},{lon});
    );
    out 5;
    """
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            if resp.status_code != 200:
                return []
            data = resp.json()
            elements = data.get("elements", [])
            places = []
            for elem in elements[:5]:
                tags = elem.get("tags", {})
                name = tags.get("name") or tags.get("amenity") or tags.get("place") or "Unnamed Community Site"
                category = tags.get("amenity") or tags.get("place") or "Facility"
                places.append({
                    "name": name,
                    "type": category.capitalize(),
                    "latitude": elem.get("lat"),
                    "longitude": elem.get("lon"),
                    "verification_priority": "Priority Monitoring Location",
                    "status_label": "Potentially exposed area — requires verification"
                })
            return places
    except Exception as exc:
        logger.debug(f"Sensitive places query skipped: {exc}")
        return []
