# VayuNet — Real Data Setup Guide

Follow these exact steps to transition VayuNet from local offline testing to live Google Earth Engine Sentinel-5P satellite observations and optional Gemini AI decision support.

---

## Step 1: Google Cloud & Earth Engine Setup

1. **Google Cloud Console**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project (e.g., `vayunet-cleanair-2026`) or choose an existing project.
   - Go to **APIs & Services > Library** and search for **Earth Engine API**.
   - Click **Enable**.

2. **Register for Earth Engine Access**:
   - Visit [signup.earthengine.google.com](https://signup.earthengine.google.com/) and register your Google Cloud Project if prompted.

3. **Authenticate via CLI**:
   - In PowerShell, run:
     ```powershell
     earthengine authenticate
     ```
   - This opens your web browser to grant OAuth2 permissions. Copy the authentication code or complete the sign-in prompt.

4. **Alternative — Service Account Authentication**:
   - Go to **IAM & Admin > Service Accounts** in Google Cloud Console.
   - Create a service account named `vayunet-gee-service`.
   - Grant role: **Earth Engine Resource Viewer / Earth Engine User**.
   - Create a JSON key and save it to your machine (e.g., `C:\secrets\gee-sa-key.json`).

---

## Step 2: Configure Environment Variables

Edit `backend/.env`:

```env
# 1. Your Google Cloud Project ID
GEE_PROJECT_ID=vayunet-cleanair-2026

# 2. If using a service account JSON, uncomment and set:
# GOOGLE_APPLICATION_CREDENTIALS=C:\secrets\gee-sa-key.json

# 3. Sentinel-5P TROPOMI Collections
GEE_NO2_COLLECTION=COPERNICUS/S5P/NRTI/L3_NO2
GEE_SO2_COLLECTION=COPERNICUS/S5P/NRTI/L3_SO2
GEE_LOOKBACK_DAYS=7

# 4. Turn OFF Demo Mode to use REAL live satellite data
VAYUNET_DEMO_MODE=false

# 5. Open-Meteo Weather (Requires NO key)
OPEN_METEO_URL=https://api.open-meteo.com/v1/forecast

# 6. (Optional) Gemini AI Decision Support Key
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-2.5-flash
```

---

## Step 3: Verify Real Data Pipeline

1. Restart the backend:
   ```powershell
   cd backend
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. Check health in your browser or PowerShell:
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health"
   ```
   **Expected Real Mode Output:**
   ```json
   {
     "status": "healthy",
     "service": "vayunet-core",
     "mode": "real",
     "gee_ready": true,
     "gee_status": "configured",
     "version": "1.1.0"
   }
   ```

3. Query coordinates (e.g., Chennai or user coordinates):
   ```powershell
   $body = @{ latitude = 13.0827; longitude = 80.2707 } | ConvertTo-Json
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/analyze" -Method Post -Body $body -ContentType "application/json"
   ```
   Verify that `pollution.source` displays `Google Earth Engine (Sentinel-5P / TROPOMI)` and `weather.source` displays `Open-Meteo`.

---

## Step 4: Run the Mobile Frontend

```powershell
cd frontend
npx vite --host 0.0.0.0 --port 5173
```
- Open `http://127.0.0.1:5173`.
- The top-right badge will display **`REAL SATELLITE`** (in emerald green).
- Allow browser location to dynamically analyze your current position!
