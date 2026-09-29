import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("vayunet.gee")

_INITIALIZED = False
_INIT_ERROR: Optional[str] = None

class GEEConfigurationError(RuntimeError):
    """Raised when Google Earth Engine credentials or configuration are missing or invalid."""
    pass

def is_gee_configured() -> Tuple[bool, Optional[str]]:
    """Checks whether GEE is initialized and ready."""
    global _INITIALIZED, _INIT_ERROR
    if _INITIALIZED:
        return True, None
    try:
        _init_ee()
        return True, None
    except Exception as exc:
        return False, str(exc)

def _init_ee():
    global _INITIALIZED, _INIT_ERROR
    if _INITIALIZED:
        return
    import ee
    project = os.getenv("GEE_PROJECT_ID")
    if not project:
        _INIT_ERROR = (
            "GEE_PROJECT_ID environment variable is missing. "
            "Please specify a Google Cloud project with Earth Engine enabled."
        )
        raise GEEConfigurationError(_INIT_ERROR)
    
    try:
        ee.Initialize(project=project)
        _INITIALIZED = True
        _INIT_ERROR = None
        logger.info(f"Earth Engine initialized successfully with project {project}")
    except Exception as exc:
        _INIT_ERROR = (
            f"Earth Engine authentication failed: {exc}. "
            "Run `earthengine authenticate` or configure GOOGLE_APPLICATION_CREDENTIALS."
        )
        raise GEEConfigurationError(_INIT_ERROR) from exc

def _query_band_stats(
    collection_id: str,
    band: str,
    lat: float,
    lon: float,
    radius_m: float,
    start_str: str,
    end_str: str
) -> Dict[str, Any]:
    import ee
    _init_ee()
    point = ee.Geometry.Point([lon, lat])
    region = point.buffer(radius_m)

    collection = (
        ee.ImageCollection(collection_id)
        .filterDate(start_str, end_str)
        .filterBounds(point)
        .select(band)
    )

    count = collection.size().getInfo()
    if not count:
        return {
            "mean": None,
            "max": None,
            "count": 0,
            "latest_observed": None,
            "collection": collection_id,
            "max_location": None
        }

    image_mean = collection.mean()
    image_max = collection.max()

    combined = image_mean.addBands(image_max.rename(f"{band}_max"))
    
    stats = combined.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.max(), sharedInputs=False),
        geometry=region,
        scale=7000,
        bestEffort=True,
        maxPixels=1_000_000,
    ).getInfo()

    mean_val = stats.get(f"{band}_mean") or stats.get(band)
    max_val = stats.get(f"{band}_max")

    # Find the coordinates of the highest concentration pixel in the region
    max_loc = None
    try:
        pixel_coords = ee.Image.pixelLonLat()
        target = image_max.addBands(pixel_coords).select([band, "latitude", "longitude"])
        max_stats = target.reduceRegion(
            reducer=ee.Reducer.max(3),
            geometry=region,
            scale=7000,
            bestEffort=True,
            maxPixels=100_000
        ).getInfo()
        if max_stats and max_stats.get("latitude") is not None and max_stats.get("longitude") is not None:
            max_loc = {
                "latitude": round(float(max_stats["latitude"]), 5),
                "longitude": round(float(max_stats["longitude"]), 5)
            }
    except Exception as e:
        logger.debug(f"Could not compute max location from GEE: {e}")

    # Retrieve timestamp of latest image
    try:
        latest_img = collection.sort("system:time_start", False).first()
        time_info = latest_img.get("system:time_start").getInfo()
        observed = (
            datetime.fromtimestamp(time_info / 1000, tz=timezone.utc).isoformat()
            if time_info else None
        )
    except Exception:
        observed = None

    return {
        "mean": mean_val,
        "max": max_val,
        "count": count,
        "latest_observed": observed,
        "collection": collection_id,
        "max_location": max_loc
    }

def get_pollution(lat: float, lon: float, lookback_days: int = 7) -> Dict[str, Any]:
    """
    Queries Sentinel-5P / TROPOMI satellite atmospheric column data for NO2 and SO2.
    Tries Near Real-Time (NRTI) first, falls back to Offline (OFFL) if NRTI is empty.
    Returns structured statistics, observation count, and latest timestamp.
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)
    s_str = start.strftime("%Y-%m-%d")
    e_str = end.strftime("%Y-%m-%d")

    radius_km = float(os.getenv("ANALYSIS_RADIUS_KM", "15"))
    radius_m = radius_km * 1000.0

    # NO2 Query
    no2_coll = os.getenv("GEE_NO2_COLLECTION", "COPERNICUS/S5P/NRTI/L3_NO2")
    no2_stats = _query_band_stats(
        no2_coll, "tropospheric_NO2_column_number_density", lat, lon, radius_m, s_str, e_str
    )
    if no2_stats["count"] == 0 and "NRTI" in no2_coll:
        offl_coll = "COPERNICUS/S5P/OFFL/L3_NO2"
        try:
            fallback = _query_band_stats(
                offl_coll, "tropospheric_NO2_column_number_density", lat, lon, radius_m, s_str, e_str
            )
            if fallback["count"] > 0:
                no2_stats = fallback
        except Exception as e:
            logger.warning(f"NO2 OFFL fallback error: {e}")

    # SO2 Query
    so2_coll = os.getenv("GEE_SO2_COLLECTION", "COPERNICUS/S5P/NRTI/L3_SO2")
    so2_stats = _query_band_stats(
        so2_coll, "SO2_column_number_density", lat, lon, radius_m, s_str, e_str
    )
    if so2_stats["count"] == 0 and "NRTI" in so2_coll:
        offl_coll = "COPERNICUS/S5P/OFFL/L3_SO2"
        try:
            fallback = _query_band_stats(
                offl_coll, "SO2_column_number_density", lat, lon, radius_m, s_str, e_str
            )
            if fallback["count"] > 0:
                so2_stats = fallback
        except Exception as e:
            logger.warning(f"SO2 OFFL fallback error: {e}")

    # Only designate a hotspot if the maximum concentration pixel is truly elevated above clean baseline
    max_loc = None
    pollutant = "NO2"
    if no2_stats.get("max") is not None and no2_stats["max"] >= 0.00008:
        max_loc = no2_stats.get("max_location")
        pollutant = "NO2"
    elif so2_stats.get("max") is not None and so2_stats["max"] >= 0.00004:
        max_loc = so2_stats.get("max_location")
        pollutant = "SO2"

    return {
        "no2": no2_stats["mean"],
        "no2_max": no2_stats["max"],
        "no2_observations": no2_stats["count"],
        "no2_latest": no2_stats["latest_observed"],
        "no2_collection": no2_stats["collection"],
        "so2": so2_stats["mean"],
        "so2_max": so2_stats["max"],
        "so2_observations": so2_stats["count"],
        "so2_latest": so2_stats["latest_observed"],
        "so2_collection": so2_stats["collection"],
        "max_location": max_loc,
        "lookback_days": lookback_days,
        "source": "Google Earth Engine (Sentinel-5P / TROPOMI)",
        "scientific_note": "Atmospheric vertical column density in mol/m^2; decision-support proxy, not surface AQI."
    }


