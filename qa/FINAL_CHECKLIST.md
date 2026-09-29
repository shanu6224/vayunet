# VayuNet — Final Acceptance Verification Checklist

Ensure every item is verified prior to demonstration:

### End-to-End Acceptance Test (Section 28)
- [x] **1. Backend Service**: FastAPI starts cleanly without dependency errors on port 8000.
- [x] **2. Frontend PWA**: Vite dev server compiles and serves on port 5173 without warnings.
- [x] **3. Dynamic Geolocation**: PWA queries `navigator.geolocation` and obtains current device coordinates.
- [x] **4. Multi-Region Support**: No hardcoded Cuddalore/Chennai/Madurai coordinates in the production pipeline; dynamically supports any location globally.
- [x] **5. Real Weather Queries**: Queries live Open-Meteo weather (wind speed, wind direction, gusts, temp, humidity, pressure).
- [x] **6. Real GEE Integration**: Sentinel-5P queries implemented via `COPERNICUS/S5P/NRTI/L3_NO2` and `L3_SO2` with `OFFL` fallback.
- [x] **7. Transparent GEE Configuration**: When GEE credentials are not configured in real mode, reports clear instructions without silent spoofing.
- [x] **8. Clear Separation of Demo Mode**: Distinct `DEMO MODE` badge and banner when `VAYUNET_DEMO_MODE=true`.
- [x] **9. Multi-factor Anomaly & Risk Engine**: Classifies risk into `LOW`, `MODERATE`, `HIGH`, `CRITICAL` with weather stagnation/dispersion modifiers.
- [x] **10. Possible Movement Advection**: Estimates downwind bearing and cardinal direction (`(wind_direction + 180) % 360`).
- [x] **11. Potential Exposure Corridor GeoJSON**: Generates downwind dispersion polygon (GeoJSON) with lateral spreading cone.
- [x] **12. Interactive Leaflet Map**: Shows user location pulse, hotspot center, wind vector line, exposure polygon, and sensitive site markers.
- [x] **13. Sensitive Facilities Verification**: Identifies nearby schools and hospitals with "Requires verification / Priority monitoring" status.
- [x] **14. Duolingo-style Status Experience**: Clear color-coded status card with concise, friendly headlines ("Air looks relatively stable", "⚠️ Pollution risk increased", etc.).
- [x] **15. Audio & Haptic Alerts**: Synthesizes custom Web Audio chime and triggers device vibration on high-risk conditions with cooldown anti-spam.
- [x] **16. Android Native Compilation**: Kotlin code compiles with 0 errors via Gradle 9 / AGP 8.7.
- [x] **17. Android Debug APK**: `app-debug.apk` built and ready for device installation.
- [x] **18. Android AppWidget**: Native `VayuWidgetProvider` (2x1 compact) displaying Risk, Pollution, Wind, and Last update with tap-to-open.
- [x] **19. Android Notifications**: Native `NotificationChannel` with high priority, custom sound, and vibration pattern.
- [x] **20. Scientific Phrasing**: All text rigorously uses "possible movement", "potential exposure", and "priority verification", avoiding claims of guaranteed plume trajectories.
