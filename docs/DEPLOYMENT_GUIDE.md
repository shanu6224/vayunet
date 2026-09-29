# VayuNet — Public HTTPS Deployment Guide

This guide describes how to deploy the existing VayuNet application to the public internet so you can send **ONE public HTTPS link** to your mentor, which opens on their Android phone as a mobile application and supports "Add to Home Screen".

---

## 1. Architecture Overview

```text
User / Mentor Android Phone
            │
            ▼ (Opens Public HTTPS Link)
   [ VayuNet Mobile PWA ]  ───►  "Add to Home Screen" (Standalone Mobile Web App)
            │
            ▼ (HTTPS POST /api/analyze with Dynamic Phone GPS)
   [ FastAPI Public Backend ]
     ├── Open-Meteo Live Weather (Wind speed/direction, temp, pressure)
     ├── Sentinel-5P Satellite / Demo Mode
     ├── Multi-Factor Risk & Dispersion Engine
     └── GeoJSON Downwind Exposure Corridor
            ▲
            │ (Periodic 30-min sync over HTTPS)
[ Native Android Home-Screen Widget ] (2x1 VayuWidgetProvider)
```

Both the **Mobile PWA** and the **Native Android Widget** connect directly to the public HTTPS backend URL. No local Wi-Fi connection is required.

---

## 2. Option A: One-Click Render Deployment (Recommended)

Render hosts both the FastAPI backend and the static frontend PWA on free tier with automatic HTTPS certificates.

### Step 1: Push Project to GitHub
Push your repository to GitHub:
```bash
git add .
git commit -m "Prepare VayuNet for public deployment"
git push origin main
```

### Step 2: Deploy with Blueprint
1. Go to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** → **Blueprint**.
3. Connect your GitHub repository.
4. Render will automatically detect [`render.yaml`](file:///c:/Users/SHAKTHI%20PRIYA/Downloads/VayuNet_FINAL_REAL_WORKING_MVP/VayuNet_REAL_WORKING_MVP/render.yaml) and configure two services:
   - **`vayunet-api`** (FastAPI Web Service)
   - **`vayunet-app`** (Static PWA Frontend)
5. Click **Apply**.

Render will deploy both services and provide two public HTTPS URLs:
- Backend: `https://vayunet-api.onrender.com`
- Frontend: `https://vayunet-app.onrender.com`

---

## 3. Option B: Manual Render Deployment

If you prefer to configure the services manually on Render:

### Service 1: FastAPI Backend (Web Service)
| Field | Value |
| :--- | :--- |
| **Type** | Web Service |
| **Name** | `vayunet-api` |
| **Runtime** | Python 3 |
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | Free |

**Environment Variables:**
- `VAYUNET_DEMO_MODE`: `true`
- `ANALYSIS_RADIUS_KM`: `15`
- `OPEN_METEO_URL`: `https://api.open-meteo.com/v1/forecast`
- `GEE_LOOKBACK_DAYS`: `7`
- `GEMINI_MODEL`: `gemini-2.5-flash`

*Copy the backend URL (e.g. `https://vayunet-api.onrender.com`).*

### Service 2: Mobile PWA (Static Site)
| Field | Value |
| :--- | :--- |
| **Type** | Static Site |
| **Name** | `vayunet-app` |
| **Root Directory** | `frontend` |
| **Build Command** | `npm install && npm run build` |
| **Publish Directory** | `dist` |

**Environment Variables:**
- `VITE_API_URL`: `https://vayunet-api.onrender.com` *(your backend URL from Service 1)*

**Rewrite Rule (under Redirects/Rewrites):**
- **Source:** `/*`
- **Destination:** `/index.html`
- **Action:** Rewrite

---

## 4. Sending the Link to Your Mentor

1. Copy your public frontend HTTPS URL:
   ```text
   https://vayunet-app.onrender.com
   ```
2. Send this single link to your mentor via WhatsApp, email, or message.

---

## 5. Mentor Experience on Android Phone

When your mentor clicks the link:

1. **Opens in Mobile Browser (Chrome)**:
   - VayuNet loads in full mobile-app portrait view.
   - Browser asks for Location Permission: Tapping **Allow** instantly reads their live device GPS.
   - The status hero card displays live risk (`AIR IS GOOD`, `BE CAREFUL`, `ATTENTION`).
   - The Humanitarian OpenStreetMap renders roads, terrain, and landmarks without watermarks.
   - Shows the user location 🔵, pollution hotspot 🔴, movement corridor 🟠, affected zone 🟡, and wind vector 🌬️.

2. **Installing as App ("Add to Home Screen")**:
   - In Chrome, tap the **three dots menu** (⋮) at top right.
   - Tap **"Add to Home Screen"** or **"Install app"**.
   - An app icon with the VayuNet leaf 🍃 will be placed on their home screen.
   - Opening it launches VayuNet in standalone fullscreen app mode without browser URL bars.

---

## 6. Native Android App & Home-Screen Widget

To test or demonstrate the real 2x1 Android home-screen widget on a physical device:

1. In [`android/app/src/main/java/com/vayunet/app/AppConfig.kt`](file:///c:/Users/SHAKTHI%20PRIYA/Downloads/VayuNet_FINAL_REAL_WORKING_MVP/VayuNet_REAL_WORKING_MVP/android/app/src/main/java/com/vayunet/app/AppConfig.kt), set `DEFAULT_API_BASE_URL` to your public backend:
   ```kotlin
   const val DEFAULT_API_BASE_URL: String = "https://vayunet-api.onrender.com"
   ```
2. Build the APK:
   ```powershell
   cd android
   .\gradlew.bat assembleDebug
   ```
3. Transfer and install [`android/app/build/outputs/apk/debug/app-debug.apk`](file:///c:/Users/SHAKTHI%20PRIYA/Downloads/VayuNet_FINAL_REAL_WORKING_MVP/VayuNet_REAL_WORKING_MVP/android/app/build/outputs/apk/debug/app-debug.apk) onto the Android phone.
4. Long-press on the Android home screen → **Widgets** → Select **VayuNet (2x1)** → Drag to home screen.
5. The widget connects directly to the public HTTPS backend over cell data or Wi-Fi, updating risk level, pollution status, and wind vectors every 30 minutes.
