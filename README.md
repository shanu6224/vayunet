# VayuNet — Hyper-local Pollution Intelligence & Climate Resilience

[![VayuNet Architecture](https://img.shields.io/badge/Architecture-FastAPI%20%7C%20PWA%20%7C%20Android%20Widget-teal)](#architecture)
[![Satellite Data](https://img.shields.io/badge/Sentinel--5P-TROPOMI%20NO2%2FSO2-blue)](#5-google-earth-engine-setup)
[![Weather API](https://img.shields.io/badge/Weather-Open--Meteo%20Live-orange)](#7-weather--wind-api)

VayuNet is a hyper-local atmospheric pollution intelligence platform designed to move beyond passive AQI numbers. It detects atmospheric column anomalies using real satellite data, calculates wind-driven downwind transport vectors, constructs potential exposure corridors, and alerts users and municipal authorities to prioritize ground-level verification and protective action.

---

## 1. What VayuNet Does

Traditional air quality apps merely display a single historical AQI number for an entire city. VayuNet answers critical operational questions:
- **Where is the current pollution anomaly?** Analyzes Sentinel-5P TROPOMI tropospheric NO₂ and SO₂ column density around the user's dynamic coordinates.
- **What is the atmospheric risk level?** Classifies conditions into `LOW`, `MODERATE`, `HIGH`, or `CRITICAL` using multi-factor anomaly scoring and meteorological modifiers (stagnation, dispersion).
- **In which direction could pollution potentially move?** Derives advective transport bearing and cardinal direction from real-time meteorological wind fields.
- **Which areas could potentially be exposed?** Generates a downstream **GeoJSON dispersion corridor** representing potential exposure zones.
- **Which nearby sites require verification?** Flags potentially exposed schools, hospitals, and populated suburbs for priority monitoring.
- **How are citizens alerted?** Delivers Duolingo-style status cards, synthesized browser audio alerts, haptic vibrations, native Android notifications, and a real 2x1 Android home-screen widget.

> **Scientific Notice:** Sentinel-5P satellite observations represent vertical column densities in mol/m², which serve as decision-support proxies rather than minute-by-minute surface AQI monitors. Downwind movement and exposure zones denote *potential transport corridors requiring priority verification*, not guaranteed ground-level plume trajectories.

---

## 2. System Architecture

```text
               +-------------------------------------------------------+
               |                    User Device                        |
               | (Dynamic Browser Geolocation / Android GPS Location)  |
               +---------------------------+---------------------------+
                                           |
                                [Lat, Lon Coordinates]
                                           v
+-----------------------------------------------------------------------------------------+
|                                  FastAPI Backend                                        |
|                                                                                         |
|  +--------------------+   +-----------------------+   +------------------------------+  |
|  |   gee_service.py   |   |  weather_service.py   |   |      places_service.py       |  |
|  | Sentinel-5P NO2/SO2|   |  Open-Meteo Wind/Temp |   |  OSM Sensitive Sites (OSM)   |  |
|  +---------+----------+   +-----------+-----------+   +--------------+---------------+  |
|            \                          |                             /                   |
|             \                         v                            /                    |
|              +-------->   risk_engine.py / analysis.py   <--------+                     |
|                           - Multi-factor anomaly score                                  |
|                           - Downwind bearing & GeoJSON                                  |
|                           - Alert deduplication / cooldown                              |
|                           - Gemini AI explainability                                    |
+---------------------------------------+-------------------------------------------------+
                                        |
                            [Structured JSON Payload]
                                        |
         +------------------------------+------------------------------+
         |                                                             |
         v                                                             v
+--------------------------------+           +--------------------------------------------+
|         Mobile PWA             |           |         Native Android System              |
| - Duolingo-style status cards  |           | - Real 2x1 AppWidget (VayuWidgetProvider)  |
| - Leaflet interactive map      |           | - WorkManager periodic refresh             |
| - GeoJSON corridor & markers   |           | - High-risk NotificationChannel with audio |
| - Web Audio synth & vibration  |           | - FCM remote alert architecture            |
+--------------------------------+           +--------------------------------------------+
```

---

## 3. Repository Structure

```text
VayuNet_REAL_WORKING_MVP/
├── backend/                        # FastAPI core engine
│   ├── app/
│   │   ├── services/
│   │   │   ├── gee_service.py      # Sentinel-5P NRTI/OFFL query & stats
│   │   │   ├── weather_service.py  # Open-Meteo wind, temp, humidity, pressure
│   │   │   ├── risk_engine.py      # Anomaly scoring & GeoJSON downwind corridor
│   │   │   ├── places_service.py   # Sensitive site identification (schools, clinics)
│   │   │   ├── gemini_service.py   # AI decision explainability & fallback
│   │   │   └── analysis.py         # Pipeline orchestration & alert cooldown
│   │   ├── main.py                 # API router (/api/analyze, /health, /status, /config)
│   │   └── __init__.py
│   ├── test_api.py                 # Automated backend test suite
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Environment template
│   └── .env                        # Local configuration
├── frontend/                       # Mobile-first PWA
│   ├── src/
│   │   ├── config.js               # Auto-resolving API host endpoint
│   │   ├── style.css               # Modern mobile design system
│   │   └── main.js                 # PWA logic, Leaflet map & alert synthesis
│   ├── public/
│   │   ├── manifest.webmanifest    # PWA installable manifest
│   │   └── sw.js                   # Service worker for offline & caching
│   ├── index.html                  # HTML5 entry with mobile meta tags
│   └── package.json                # Vite & Leaflet dependencies
├── android/                        # Native Android Application & Widget
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/com/vayunet/app/
│   │   │   │   ├── MainActivity.kt               # Companion activity & permission handler
│   │   │   │   ├── VayuWidgetProvider.kt         # Native Android AppWidgetProvider
│   │   │   │   ├── VayuWidgetWorker.kt           # WorkManager background updater
│   │   │   │   ├── NotificationHelper.kt         # Android NotificationChannel & sound
│   │   │   │   └── VayuFirebaseMessagingService.kt # FCM remote push handler
│   │   │   ├── res/
│   │   │   │   ├── layout/vayunet_widget.xml     # Compact 2x1 widget layout
│   │   │   │   ├── layout/activity_main.xml      # Native test dashboard
│   │   │   │   └── xml/vayunet_widget_info.xml   # AppWidget metadata
│   │   │   └── AndroidManifest.xml               # Permissions & receivers
│   │   └── build.gradle                          # Android application gradle config
│   ├── build.gradle                              # Root gradle configuration
│   ├── settings.gradle                           # Project settings
│   ├── gradle.properties                         # AndroidX & JVM configuration
│   └── gradlew.bat                               # Gradle wrapper executable
├── docs/
│   └── REAL_DATA_SETUP.md          # Step-by-step setup guide for live satellite data
├── qa/
│   └── FINAL_CHECKLIST.md          # Field testing & presentation checklist
└── README.md
```

---

## 4. Prerequisites

- **Python**: 3.10 to 3.14
- **Node.js**: v18+ (tested on Node v24)
- **JDK**: Java 17+ (tested on OpenJDK 25)
- **Android SDK**: API 26 to 35 (installed via Android Studio or command-line tools)

---

## 5. Google Earth Engine Setup

VayuNet accesses the European Space Agency Sentinel-5P collections:
- `COPERNICUS/S5P/NRTI/L3_NO2` (tropospheric NO₂ column density)
- `COPERNICUS/S5P/NRTI/L3_SO2` (SO₂ column density)
*(Includes automated fallback to `OFFL` collections if NRTI observations are unavailable).*

### Steps:
1. Create or select a Google Cloud Project with the **Earth Engine API** enabled.
2. In PowerShell, authenticate your local machine:
   ```powershell
   earthengine authenticate
   ```
3. Set your project ID in `backend/.env`:
   ```env
   GEE_PROJECT_ID=your-gcp-project-id
   ```
4. Alternatively, use a Service Account key:
   ```env
   GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account.json
   ```

*Note: If GEE credentials are not configured, VayuNet returns a clear diagnostic message. You can toggle `VAYUNET_DEMO_MODE=true` in `backend/.env` for offline UI testing.*

---

## 6. Environment Variables

Configure `backend/.env`:

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `GEE_PROJECT_ID` | GCP Project ID with Earth Engine API enabled | `your-project-id` |
| `GEE_LOOKBACK_DAYS` | Satellite observation search window | `7` |
| `VAYUNET_DEMO_MODE` | Toggle offline testing mode | `false` (real mode) / `true` |
| `OPEN_METEO_URL` | Weather API endpoint | `https://api.open-meteo.com/v1/forecast` |
| `GEMINI_API_KEY` | Optional: Gemini API Key for AI explanations | *(optional)* |
| `GEMINI_MODEL` | Gemini model name | `gemini-2.5-flash` |

---

## 7. Weather & Wind API

- VayuNet queries **Open-Meteo** in real time based on the user's dynamic coordinates.
- **No API key is required.**
- Extracted parameters: Wind Speed (10m), Wind Direction (10m), Wind Gusts, Temperature (2m), Relative Humidity, Surface Pressure, and Precipitation.

---

## 8. Gemini Setup (Optional)

Gemini provides human-action explainability for decision makers.
1. Obtain an API key from Google AI Studio.
2. Set in `backend/.env`:
   ```env
   GEMINI_API_KEY=AIzaSy...
   ```
3. If omitted, VayuNet automatically uses its deterministic scientific explainability fallback.

---

## 9. Firebase Cloud Messaging Setup (Optional)

For remote cloud push alerts:
1. Create a Firebase project and add Android app package `com.vayunet.app`.
2. Download `google-services.json` and place it in `android/app/`.
3. The native application includes `VayuFirebaseMessagingService.kt` to parse push alerts, trigger notifications with sound/vibration, and refresh the home-screen widget.

---

## 10. Backend Startup

1. Open PowerShell and navigate to `backend/`:
   ```powershell
   cd backend
   ```
2. Run the automated test suite:
   ```powershell
   python test_api.py
   ```
3. Launch the FastAPI server:
   ```powershell
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
4. Verify endpoints:
   - Health: `http://127.0.0.1:8000/api/health`
   - Status: `http://127.0.0.1:8000/api/status`
   - Config: `http://127.0.0.1:8000/api/config`

---

## 11. Frontend Startup (PWA)

1. Open a new terminal and navigate to `frontend/`:
   ```powershell
   cd frontend
   npm install
   npm run build
   ```
2. Start the development server (accessible to mobile devices on local Wi-Fi):
   ```powershell
   npx vite --host 0.0.0.0 --port 5173
   ```
3. Open in your browser: `http://127.0.0.1:5173`
   - Allow location access to analyze your current physical location.
   - Or test any city using the **Active Analysis Point** dropdown (Chennai, Madurai, Cuddalore, Thoothukudi, Mettur).

---

## 12. Android Native Build

The native Android app and home-screen widget are pre-compiled and tested.

1. Navigate to `android/`:
   ```powershell
   cd android
   ```
2. Build the Debug APK:
   ```powershell
   .\gradlew.bat assembleDebug
   ```
3. The APK will be generated at:
   `android/app/build/outputs/apk/debug/app-debug.apk`

---

## 13. Widget Installation on Phone

1. Install `app-debug.apk` on an Android phone or emulator:
   ```powershell
   adb install -r android/app/build/outputs/apk/debug/app-debug.apk
   ```
2. Launch the **VayuNet** app on the phone once to grant location and notification permissions.
3. Return to the phone's home screen.
4. Long-press on any empty space on your home screen and tap **Widgets**.
5. Locate **VayuNet** and drag the 2x1 widget onto your home screen.
6. The widget displays:
   - `🌍 VayuNet`
   - `Air Risk: HIGH ⚠️`
   - `Pollution: Elevated`
   - `Wind: SE`
   - `Last update: 10:42 AM`
7. Tap the widget at any time to open the live interactive PWA.

---

## 14. Testing & Verification

1. **Dynamic Geolocation**: Change your location in browser DevTools or select different cities from the dropdown. Verify that coordinates, wind vectors, and analysis results change dynamically without hardcoded coordinates.
2. **Alert Trigger**: When risk is `HIGH` or `CRITICAL`, verify the Duolingo-style banner, the synthesized chime audio, and device vibration.
3. **Interactive Map**: Verify the blue pulsing user marker, the hotspot center, the dashed wind transport vector, and the GeoJSON potential exposure polygon.
4. **Android Widget**: Tap "Refresh Home-Screen Widget Now" in `MainActivity` and verify the widget updates its status and timestamp.

---

## 15. Known Platform Limitations

- **Browser Geolocation**: Geolocation requires an HTTPS connection or `localhost`/`127.0.0.1`. When accessing across local Wi-Fi via raw IP, use the built-in city selector dropdown if browser security blocks geolocation.
- **Audio Autoplay**: Modern browsers require at least one user interaction (such as tapping "Enable Alert Sound") before Web Audio synthesis can play automatically.
- **Background Restrictions**: Android OS power management restricts background network requests to WorkManager periodic intervals (~15–30 minutes) rather than continuous polling.
