# Google Earth Engine (GEE) & Sentinel-5P Setup Guide for VayuNet

This guide explains how Google Earth Engine (GEE) connects to European Space Agency Sentinel-5P/TROPOMI satellite data in VayuNet, how to configure project credentials, and the distinction between **REAL MODE** and **DEMO MODE**.

---

## 1. Overview of Satellite Data Used

VayuNet uses high-resolution satellite atmospheric observations from the **Sentinel-5P / TROPOMI** instrument:
- **NO₂ (Nitrogen Dioxide)**: `COPERNICUS/S5P/NRTI/L3_NO2` (Near Real-Time) and `COPERNICUS/S5P/OFFL/L3_NO2` (Offline fallback). Band: `tropospheric_NO2_column_number_density` (mol/m²).
- **SO₂ (Sulfur Dioxide)**: `COPERNICUS/S5P/NRTI/L3_SO2` (Near Real-Time) and `COPERNICUS/S5P/OFFL/L3_SO2` (Offline fallback). Band: `SO2_column_number_density` (mol/m²).

These data represent vertical column densities throughout the troposphere. In VayuNet, they serve as objective anomaly detection inputs to calculate risk scores and locate distinct pollution hotspots.

---

## 2. REAL MODE vs. DEMO MODE

| Feature | REAL SATELLITE MODE | DEMO MODE (Testing) |
|---|---|---|
| **Environment setting** | `VAYUNET_DEMO_MODE=false` | `VAYUNET_DEMO_MODE=true` |
| **Data source** | Live Sentinel-5P via Earth Engine API | Controlled synthetic satellite proxy data |
| **Authentication required** | Google Cloud Project with GEE enabled | None required |
| **Weather source** | Live Open-Meteo real-time weather | Live Open-Meteo real-time weather |
| **UI Badge** | `🟢 REAL SATELLITE` / `நேரடி செயற்கைக்கோள்` | `🟡 DEMO MODE` / `மாதிரி முறை (DEMO)` |
| **Use case** | Field deployment, real intelligence | Offline evaluation, UI walkthroughs |

> [!IMPORTANT]
> DEMO values are never presented as real satellite observations. The badge and data source explicitly declare `DEMO MODE` whenever demo mode is active.

---

## 3. Required Environment Variables

Configure these in `backend/.env`:

```env
# 1. Google Cloud Project ID with Earth Engine API enabled
GEE_PROJECT_ID=your-gcp-project-id

# 2. (Optional) Path to Service Account JSON key (if not using OAuth2 CLI login)
# GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account-key.json

# 3. Sentinel-5P Image Collections
GEE_NO2_COLLECTION=COPERNICUS/S5P/NRTI/L3_NO2
GEE_SO2_COLLECTION=COPERNICUS/S5P/NRTI/L3_SO2
GEE_LOOKBACK_DAYS=7

# 4. Mode Selection: set to false for real Earth Engine data
VAYUNET_DEMO_MODE=false

# 5. Open-Meteo Weather URL
OPEN_METEO_URL=https://api.open-meteo.com/v1/forecast
```

---

## 4. How to Authenticate Google Earth Engine

### Option A: Local Developer Authentication (Interactive)

1. Open PowerShell and run:
   ```powershell
   earthengine authenticate
   ```
2. Your browser will open the Google Sign-in page. Select your Google account that has Earth Engine access.
3. Grant permissions. A token is automatically stored in `~/.config/earthengine/credentials`.
4. Ensure `GEE_PROJECT_ID` in `backend/.env` matches your Google Cloud project.

### Option B: Automated / Production Service Account Authentication

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Navigate to **IAM & Admin > Service Accounts**.
3. Create a service account (e.g. `vayunet-gee-engine@<project>.iam.gserviceaccount.com`).
4. Grant the role **Earth Engine Resource Viewer** (or **Earth Engine User**).
5. In **Keys**, create a new JSON key and download it.
6. Set the path in `backend/.env`:
   ```env
   GOOGLE_APPLICATION_CREDENTIALS=C:\Users\SHAKTHI PRIYA\Downloads\vayunet-sa-key.json
   ```

---

## 5. Graceful Degradation (User Safety)

When Earth Engine credentials are not configured or when an area has temporary cloud obstruction:
- The app **does NOT** crash or expose raw exception tracebacks to ordinary village users.
- The public UI simply states:
  - English: *"Satellite data is temporarily unavailable."*
  - Tamil: *"செயற்கைக்கோள் தரவு தற்காலிகமாக கிடைக்கவில்லை."*
- Real-time weather analysis (wind speed, wind direction, temperature, humidity) and movement vectors remain **100% active** via Open-Meteo.
- Developers and judges can inspect the collapsible **"Technical details"** section to view the diagnostic message (`gee_diagnostic`) without confusing ordinary users.
