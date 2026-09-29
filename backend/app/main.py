import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

from .services.analysis import analyze_location
from .services.gee_service import is_gee_configured

app = FastAPI(
    title="VayuNet API",
    description="Hyper-local Pollution Intelligence & Climate Resilience API",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import Optional

class LocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 longitude")
    demo: Optional[bool] = Field(None, description="Optional override for demo mode")

@app.get("/api/health")
def health():
    gee_ok, gee_err = is_gee_configured()
    demo_active = os.getenv("VAYUNET_DEMO_MODE", "false").lower() == "true"
    return {
        "status": "healthy",
        "service": "vayunet-core",
        "mode": "demo" if demo_active else "real",
        "gee_ready": gee_ok,
        "gee_status": "configured" if gee_ok else (gee_err or "unconfigured"),
        "version": "1.1.0"
    }

@app.get("/api/status")
def system_status():
    demo_active = os.getenv("VAYUNET_DEMO_MODE", "false").lower() == "true"
    gee_ok, _ = is_gee_configured()
    gemini_key = os.getenv("GEMINI_API_KEY")
    return {
        "mode": "demo" if demo_active else "real",
        "services": {
            "satellite_sentinel_5p": "demo_fallback" if demo_active else ("active" if gee_ok else "credentials_required"),
            "weather_open_meteo": "active",
            "gemini_explanation": "active" if gemini_key else "deterministic_fallback",
            "sensitive_places_osm": "active"
        }
    }

@app.get("/api/config")
def client_config():
    demo_active = os.getenv("VAYUNET_DEMO_MODE", "false").lower() == "true"
    return {
        "app_name": "VayuNet",
        "tagline": "Hyper-local Pollution Intelligence & Climate Resilience",
        "mode": "demo" if demo_active else "real",
        "refresh_interval_ms": 300000  # 5 minutes
    }

@app.post("/api/analyze")
async def analyze(req: LocationRequest):
    try:
        return await analyze_location(req.latitude, req.longitude, demo_override=req.demo)
    except RuntimeError as rerr:
        raise HTTPException(status_code=503, detail=str(rerr))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Analysis pipeline error: {exc}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)


