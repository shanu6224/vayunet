# VayuNet: Mobile Testing & Notification Architecture Guide

This guide details how to test the VayuNet Android Application, Home-Screen Widget, PWA, and push notification architecture both locally on your development Wi-Fi network and in production via Firebase Cloud Messaging (FCM).

---

## 1. Local Phone Testing (Wi-Fi Development Mode)

When developing and testing on a physical Android device, **`localhost` inside Android refers to the phone itself**, NOT your laptop.

### Step 1: Connect Phone & Laptop to the Same Wi-Fi Network
Make sure both your development computer and physical Android smartphone are connected to the same local Wi-Fi router or mobile hotspot.

### Step 2: Find Your Laptop's Local IP Address
Run this in PowerShell on your laptop:
```powershell
ipconfig
```
Look for **IPv4 Address** under your active Wi-Fi adapter (for example: `192.168.1.9`).

### Step 3: Start the Backend and Frontend with Host Binding
The servers must bind to `0.0.0.0` so incoming connections from other devices on the Wi-Fi network are accepted.

- **FastAPI Backend (Port 8000)**:
  ```powershell
  cd backend
  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```
- **Vite Frontend / PWA (Port 5173)**:
  ```powershell
  cd frontend
  npx vite --host 0.0.0.0 --port 5173
  ```

---

## 2. Real Android Application & Home-Screen Widget

The VayuNet Android module is a **native compiled Android application** (`app-debug.apk`), built using Kotlin, Jetpack WorkManager, Android AppWidgetProvider, and Android Notification Channels.

### Installing the APK on Your Phone
The compiled APK is located at:
```
android/app/build/outputs/apk/debug/app-debug.apk
```

You can install it either via ADB:
```powershell
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```
Or by copying `app-debug.apk` to your phone via USB or WhatsApp/Drive and tapping **Install**.

### In-App Configuration
1. Open **VayuNet** on your Android phone.
2. In the **Backend API Base URL** field, enter your laptop's Wi-Fi IP:
   ```
   http://192.168.1.9:8000
   ```
   *(If using Android Studio Emulator, leave as default `http://10.0.2.2:8000`)*.
3. Tap **Save API URL**.
4. Tap **📍 Check Surrounding Pollution**:
   - The app requests GPS/Network permissions.
   - It queries your backend with your live coordinates.
   - It displays real analysis: Air status, separate pollution hotspot (distance & direction), wind movement, and plain-language advisory.
5. Tap **🗺️ Open Interactive PWA Map** to open the live Leaflet map in your phone's browser at `http://192.168.1.9:5173`.

### Placing the Real Home-Screen Widget
1. Go to your phone's home screen.
2. Long-press on any empty space.
3. Tap **Widgets**.
4. Scroll to **VayuNet** and drag the 3×2 widget to your home screen.
5. The widget displays live data:
   ```
   VayuNet                      Updated: 6:40 PM
   🔴 HIGH RISK
   Pollution may move toward you.
   Wind: SE
   ```
6. The widget refreshes automatically via `WorkManager` periodically every 30 minutes, or instantly whenever you tap **🔄 Refresh Home-Screen Widget** or tap the widget itself.

---

## 3. Notification Reality: Local vs Remote Push

VayuNet clearly distinguishes between **Local Test Mode** and **Production Remote Push Mode**.

### Mode A: Local Test Mode (Active)
- **Mechanism**: The Android app requests `POST_NOTIFICATIONS` permission (Android 13+) and registers the `vayunet_pollution_alerts` notification channel with high priority, custom notification sound, and vibration pattern (`[0, 250, 150, 250]`).
- **Trigger**:
  - Tapping **⚠️ Test Native Alert Notification** in the app.
  - Or when `WorkManager` detects `HIGH` or `CRITICAL` risk with downwind movement toward the user.
- **Notification Presentation**:
  - **Title**: `⚠️ VayuNet Alert`
  - **Body**: `Pollution may move toward your area. Possible direction: South-East`
  - **Sound & Vibration**: Rings default alert chime and vibrates.
  - **Action**: Tapping the notification opens the VayuNet application.

### Mode B: Production Remote Alert Mode (Firebase Cloud Messaging)
In production, satellite passes over large regions are processed on the server without waiting for user polling. When a hazardous plume is detected:

```
[Sentinel-5P Anomaly] -> [VayuNet Server] -> [FCM HTTP v1 API] -> [Firebase Cloud] -> [Android Device] -> [Notification + Widget Sync]
```

#### Steps to Activate Remote Push:
1. **Create Firebase Project**:
   - Go to [Firebase Console](https://console.firebase.google.com/).
   - Add an Android App with package name: `com.vayunet.app`.
   - Download `google-services.json` and place it in `android/app/google-services.json`.
2. **Apply Google Services Plugin**:
   - In `android/build.gradle`:
     ```groovy
     plugins {
         id 'com.google.gms.google-services' version '4.4.2' apply false
     }
     ```
   - In `android/app/build.gradle`:
     ```groovy
     plugins {
         id 'com.android.application'
         id 'org.jetbrains.kotlin.android'
         id 'com.google.gms.google-services'
     }
     dependencies {
         implementation 'com.google.firebase:firebase-messaging-ktx:24.1.0'
     }
     ```
3. **Register Service in `AndroidManifest.xml`**:
   ```xml
   <service
       android:name=".VayuFirebaseMessagingService"
       android:exported="false">
       <intent-filter>
           <action android:name="com.google.firebase.MESSAGING_EVENT" />
       </intent-filter>
   </service>
   ```
4. **Backend Push Dispatch**:
   The VayuNet backend dispatches push notifications via Google Service Account credentials:
   ```python
   # Sample backend FCM dispatch snippet
   import firebase_admin
   from firebase_admin import messaging

   message = messaging.Message(
       data={
           "risk_level": "HIGH",
           "message": "Pollution may move toward your area.",
           "movement": "South-East"
       },
       topic="pollution_alerts_zone_4"
   )
   messaging.send(message)
   ```

---

## 4. Testing the 5 Core Product Scenarios

To verify system behavior across all edge cases without waiting for live satellite passes:

### Scenario A: Clean Atmosphere / Stable Conditions
- **Condition**: Atmospheric gas levels below background threshold (e.g. NO₂ < 0.0001 mol/m²).
- **Behavior**:
  - UI Status: `🟢 Air conditions look stable.` (தமிழ்: `காற்று நிலை இயல்பாக உள்ளது.`)
  - Hotspot: `🟢 No clear hotspot detected`
  - Advisory: No urgent alert; air is clear.

### Scenario B: Nearby Hotspot Blowing Away from User
- **Condition**: Hotspot detected 5 km North-East; wind is blowing toward North-East (away from user at South-West).
- **Behavior**:
  - UI Status: `🟡 Nearby pollution detected.`
  - Advisory: `Current wind does not indicate movement toward your area.`
  - Map: Hotspot marker 🔴 appears at Area B, arrow ➡️ points away from user 🔵.
  - User is NOT placed in the exposure zone.

### Scenario C: Nearby Hotspot Blowing Toward User (Critical Alert)
- **Condition**: Hotspot detected 5 km North-East; wind is blowing South-West (toward user).
- **Behavior**:
  - UI Status: `🔴 HIGH POLLUTION RISK` (தமிழ்: `🔴 அதிக காற்று மாசு அபாயம்`)
  - Advisory: `Pollution may move toward your area. Please check local official advisories.` (தமிழ்: `மாசு உங்கள் பகுதியை நோக்கி நகர வாய்ப்பு உள்ளது.`)
  - Map: Arrow ➡️ points directly toward user 🔵; user falls within the orange exposure polygon 🟠.
  - Notification: Native notification chimes and vibrates phone.

### Scenario D: Google Earth Engine Unavailable Fallback
- **Condition**: Network disruption or GEE offline.
- **Behavior**:
  - Ordinary village users see a friendly, non-technical message:
    `"Satellite data is temporarily unavailable."`
  - The UI does NOT show raw errors like `GEE_PROJECT_ID missing` or Python stack traces.
  - Technical error details remain strictly in the collapsible Technical Details panel.

### Scenario E: Weather Service Unavailable Fallback
- **Condition**: Weather API timeout.
- **Behavior**:
  - UI displays `"Wind data unavailable"` rather than inventing fake wind speeds or directions.
  - Fallback risk scoring accounts for missing meteorological data gracefully.

---

## 5. Summary of Built Artifacts

| Component | Technology | Artifact / Path |
| :--- | :--- | :--- |
| **Android APK** | Kotlin, Jetpack, WorkManager | `android/app/build/outputs/apk/debug/app-debug.apk` |
| **Android AppWidget** | AppWidgetProvider, RemoteViews | `VayuWidgetProvider.kt`, `R.layout.vayunet_widget` |
| **Native Notifications** | NotificationCompat, Vibration | `NotificationHelper.kt` (`vayunet_pollution_alerts`) |
| **PWA Web Frontend** | Vanilla JS/CSS, Leaflet 1.9.4 | `frontend/dist/`, `frontend/src/` |
| **FastAPI Backend** | Python 3.12, GEE, Open-Meteo | `backend/app/` (Port 8000, host `0.0.0.0`) |
