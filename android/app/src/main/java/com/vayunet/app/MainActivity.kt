package com.vayunet.app

import android.Manifest
import android.app.Activity
import android.appwidget.AppWidgetManager
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.location.Location
import android.location.LocationManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.provider.Settings
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MainActivity : Activity() {

    private lateinit var editApiUrl: EditText
    private lateinit var txtLocation: TextView
    private lateinit var txtLocationWarning: TextView
    private lateinit var btnRetryLocation: Button
    private lateinit var btnEnableGps: Button
    private lateinit var txtDebugCoords: TextView
    private lateinit var txtDebugAccuracy: TextView
    private lateinit var txtDebugTimestamp: TextView
    private lateinit var txtDebugProvider: TextView
    private lateinit var statusView: TextView
    private lateinit var txtHotspot: TextView
    private lateinit var txtMovement: TextView
    private lateinit var txtAdvice: TextView
    private lateinit var detailsView: TextView

    private var currentLat: Double = 0.0
    private var currentLon: Double = 0.0

    private lateinit var fusedLocationClient: FusedLocationProviderClient
    private var isLocating: Boolean = false
    private var activeLocationCallback: LocationCallback? = null
    private val locationTimeoutHandler = Handler(Looper.getMainLooper())
    private var locationTimeoutRunnable: Runnable? = null
    private var activeCts: CancellationTokenSource? = null

    companion object {
        private const val PERMISSION_REQUEST_CODE = 101
        private const val MAX_LOCATION_AGE_MS = 3 * 60 * 1000L // 3 minutes max age for fresh location
        private const val MAX_ACCEPTABLE_ACCURACY_METERS = 2000f // Reject wild cell towers > 2km
        private const val LOCATION_TIMEOUT_MS = 12000L
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Initialize Google Play Services Fused Location Client
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this)

        // Initialize Native Notification Channel
        NotificationHelper.createNotificationChannel(this)

        // Bind Views
        editApiUrl = findViewById(R.id.editApiUrl)
        val btnSaveApi = findViewById<Button>(R.id.btnSaveApi)
        val btnCheckLocation = findViewById<Button>(R.id.btnCheckLocation)
        txtLocation = findViewById(R.id.txtLocation)
        txtLocationWarning = findViewById(R.id.txtLocationWarning)
        btnRetryLocation = findViewById(R.id.btnRetryLocation)
        btnEnableGps = findViewById(R.id.btnEnableGps)
        txtDebugCoords = findViewById(R.id.txtDebugCoords)
        txtDebugAccuracy = findViewById(R.id.txtDebugAccuracy)
        txtDebugTimestamp = findViewById(R.id.txtDebugTimestamp)
        txtDebugProvider = findViewById(R.id.txtDebugProvider)
        statusView = findViewById(R.id.status)
        txtHotspot = findViewById(R.id.txtHotspot)
        txtMovement = findViewById(R.id.txtMovement)
        txtAdvice = findViewById(R.id.txtAdvice)
        detailsView = findViewById(R.id.details)
        val btnReportCitizenObs = findViewById<Button>(R.id.btnReportCitizenObs)
        val btnOpenPwa = findViewById<Button>(R.id.btnOpenPwa)
        val btnTestAlert = findViewById<Button>(R.id.btnTestAlert)
        val btnUpdateWidget = findViewById<Button>(R.id.btnUpdateWidget)

        // Load saved preferences for API Base URL
        val prefs = getSharedPreferences("vayunet_prefs", Context.MODE_PRIVATE)
        val savedApiUrl = prefs.getString("api_base_url", AppConfig.DEFAULT_API_BASE_URL) ?: AppConfig.DEFAULT_API_BASE_URL
        editApiUrl.setText(savedApiUrl)

        // Initial UI State: Strictly require fresh device location fix (no hardcoded fallback)
        txtLocation.text = "📍 Your Location: Acquiring fresh GPS fix..."
        txtLocation.setTextColor(Color.parseColor("#99F6E4"))
        txtDebugCoords.text = "Coordinates: Awaiting fresh device GPS fix..."
        txtDebugAccuracy.text = "Accuracy: —"
        txtDebugTimestamp.text = "Timestamp: —"
        txtDebugProvider.text = "Provider / Source: Google Play Services FusedLocationProviderClient"

        // Save API URL
        btnSaveApi.setOnClickListener {
            val url = editApiUrl.text.toString().trim()
            if (url.isNotEmpty()) {
                prefs.edit().putString("api_base_url", url).apply()
                Toast.makeText(this, "API Base URL saved: $url", Toast.LENGTH_SHORT).show()
            }
        }

        // Check Location & Trigger Analysis (User manually refreshes location)
        btnCheckLocation.setOnClickListener {
            acquireLocationAndAnalyze()
        }

        // Retry Location button
        btnRetryLocation.setOnClickListener {
            acquireLocationAndAnalyze()
        }

        // Enable GPS button (opens device settings)
        btnEnableGps.setOnClickListener {
            try {
                val intent = Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS)
                startActivity(intent)
            } catch (e: Exception) {
                Toast.makeText(this, "Could not open Location Settings: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }

        // Report Visible Pollution (passes verified live GPS coordinates and triggers observation module)
        btnReportCitizenObs.setOnClickListener {
            val baseUrl = getSavedBaseUrl()
            val basePwaUrl = if (baseUrl.contains(":8000")) {
                baseUrl.replace(":8000", ":5173")
            } else {
                AppConfig.DEFAULT_PWA_URL
            }
            val sep = if (basePwaUrl.contains("?")) "&" else "?"
            val reportUrl = if (currentLat != 0.0 && currentLon != 0.0) {
                "$basePwaUrl${sep}lat=$currentLat&lon=$currentLon&action=report"
            } else {
                "$basePwaUrl${sep}action=report"
            }
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(reportUrl))
            try {
                startActivity(intent)
            } catch (e: Exception) {
                Toast.makeText(this, "Could not open browser: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }

        // Open PWA in browser (passes fresh verified device coordinates)
        btnOpenPwa.setOnClickListener {
            val baseUrl = getSavedBaseUrl()
            val basePwaUrl = if (baseUrl.contains(":8000")) {
                baseUrl.replace(":8000", ":5173")
            } else {
                AppConfig.DEFAULT_PWA_URL
            }
            val pwaUrl = if (currentLat != 0.0 && currentLon != 0.0) {
                val sep = if (basePwaUrl.contains("?")) "&" else "?"
                "$basePwaUrl${sep}lat=$currentLat&lon=$currentLon"
            } else {
                basePwaUrl
            }
            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(pwaUrl))
            try {
                startActivity(intent)
            } catch (e: Exception) {
                Toast.makeText(this, "Could not open browser: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }

        // Test Native High-Risk Alert
        btnTestAlert.setOnClickListener {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                    ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.POST_NOTIFICATIONS), 102)
                    Toast.makeText(this, "Notification permission required. Please grant it and retry.", Toast.LENGTH_SHORT).show()
                    return@setOnClickListener
                }
            }
            NotificationHelper.showRiskNotification(
                this,
                "HIGH",
                "High pollution risk signal detected. Pollution may move toward your area.",
                "South-East"
            )
            Toast.makeText(this, "Fired native alert with sound & vibration.", Toast.LENGTH_SHORT).show()
        }

        // Trigger Immediate Widget Update / Pin Widget
        btnUpdateWidget.setOnClickListener {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                try {
                    val appWidgetManager = getSystemService(AppWidgetManager::class.java)
                    val myProvider = ComponentName(this, VayuWidgetProvider::class.java)
                    if (appWidgetManager != null && appWidgetManager.isRequestPinAppWidgetSupported) {
                        appWidgetManager.requestPinAppWidget(myProvider, null, null)
                    }
                } catch (_: Exception) {}
            }
            val workRequest = OneTimeWorkRequestBuilder<VayuWidgetWorker>().build()
            WorkManager.getInstance(this).enqueue(workRequest)
            Toast.makeText(this, "Widget background sync queued.", Toast.LENGTH_SHORT).show()
        }

        // Check Permissions & start initial GPS acquisition
        checkAndRequestPermissions()
    }

    override fun onResume() {
        super.onResume()
        // If location is not yet acquired and GPS was just turned on, refresh
        if (currentLat == 0.0 && currentLon == 0.0 && !isLocating) {
            val fineGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
            val coarseGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED
            if (fineGranted || coarseGranted) {
                acquireLocationAndAnalyze()
            }
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        stopActiveLocationUpdates()
    }

    private fun getSavedBaseUrl(): String {
        val prefs = getSharedPreferences("vayunet_prefs", Context.MODE_PRIVATE)
        return prefs.getString("api_base_url", AppConfig.DEFAULT_API_BASE_URL)?.trimEnd('/') ?: AppConfig.DEFAULT_API_BASE_URL
    }

    private fun isLocationServicesEnabled(): Boolean {
        val lm = getSystemService(Context.LOCATION_SERVICE) as? LocationManager ?: return false
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            lm.isLocationEnabled
        } else {
            lm.isProviderEnabled(LocationManager.GPS_PROVIDER) ||
            lm.isProviderEnabled(LocationManager.NETWORK_PROVIDER)
        }
    }

    private fun checkAndRequestPermissions() {
        val permissionsToRequest = mutableListOf<String>()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        val fineGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        val coarseGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED

        if (!fineGranted || !coarseGranted) {
            permissionsToRequest.add(Manifest.permission.ACCESS_FINE_LOCATION)
            permissionsToRequest.add(Manifest.permission.ACCESS_COARSE_LOCATION)
        }

        if (permissionsToRequest.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, permissionsToRequest.toTypedArray(), PERMISSION_REQUEST_CODE)
        } else {
            acquireLocationAndAnalyze()
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_CODE) {
            val fineGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
            val coarseGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED

            if (fineGranted || coarseGranted) {
                if (!fineGranted) {
                    txtLocationWarning.text = "⚠️ Approximate location granted. Precise Location is recommended for accurate hyper-local pollution intelligence."
                    txtLocationWarning.visibility = View.VISIBLE
                } else {
                    txtLocationWarning.visibility = View.GONE
                }
                acquireLocationAndAnalyze()
            } else {
                handleLocationFailure("Location permission required. Please grant location permissions in App Settings to detect your area.")
            }
        }
    }

    private fun acquireLocationAndAnalyze() {
        if (isLocating) return

        // 1. Verify Location Services (GPS) are enabled
        if (!isLocationServicesEnabled()) {
            handleLocationFailure("Location services (GPS) are turned off. Please enable Location in Android settings to get hyper-local pollution intelligence.")
            return
        }

        // 2. Verify Permissions
        val fineGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        val coarseGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED

        if (!fineGranted && !coarseGranted) {
            checkAndRequestPermissions()
            return
        }

        isLocating = true
        txtLocation.text = "📍 Acquiring fresh device GPS coordinates..."
        txtLocation.setTextColor(Color.parseColor("#99F6E4"))
        txtLocationWarning.visibility = View.GONE
        btnRetryLocation.visibility = View.GONE
        btnEnableGps.visibility = View.GONE

        txtDebugCoords.text = "Coordinates: Requesting fresh fix from GPS hardware..."
        txtDebugAccuracy.text = "Accuracy: Resolving satellites..."
        txtDebugTimestamp.text = "Timestamp: Active request in progress..."
        txtDebugProvider.text = "Provider: Google Play Services FusedLocationProviderClient"

        statusView.text = "Acquiring GPS fix..."
        statusView.setTextColor(Color.parseColor("#99F6E4"))
        txtHotspot.text = "Waiting for verified device location..."
        txtMovement.text = "Waiting for verified device location..."
        txtAdvice.text = "Obtaining high-accuracy fix via Google Play Services..."

        val priority = if (fineGranted) Priority.PRIORITY_HIGH_ACCURACY else Priority.PRIORITY_BALANCED_POWER_ACCURACY
        val cts = CancellationTokenSource()
        activeCts = cts

        // Arm safety timeout (12s)
        locationTimeoutRunnable?.let { locationTimeoutHandler.removeCallbacks(it) }
        val timeoutRunnable = Runnable {
            stopActiveLocationUpdates()
            isLocating = false
            handleLocationFailure("Unable to get your current location. GPS fix timed out. Please try again.")
        }
        locationTimeoutRunnable = timeoutRunnable
        locationTimeoutHandler.postDelayed(timeoutRunnable, LOCATION_TIMEOUT_MS)

        // Primary: getCurrentLocation for a guaranteed fresh fix (not stale cached getLastLocation)
        try {
            fusedLocationClient.getCurrentLocation(priority, cts.token)
                .addOnSuccessListener { loc: Location? ->
                    if (isValidFreshLocation(loc)) {
                        cleanUpTimeout()
                        isLocating = false
                        handleLocationSuccess(loc!!)
                    } else {
                        // If getCurrentLocation is null (GPS warming up), request an active single update
                        requestActiveSingleUpdate(priority)
                    }
                }
                .addOnFailureListener {
                    // Fall back to active location update request
                    requestActiveSingleUpdate(priority)
                }
        } catch (e: SecurityException) {
            cleanUpTimeout()
            isLocating = false
            handleLocationFailure("Location permission error: ${e.localizedMessage}")
        }
    }

    private fun requestActiveSingleUpdate(priority: Int) {
        try {
            val locationRequest = LocationRequest.Builder(priority, 1000L)
                .setMinUpdateIntervalMillis(500L)
                .setMaxUpdates(1)
                .setDurationMillis(8000L)
                .build()

            val callback = object : LocationCallback() {
                override fun onLocationResult(result: LocationResult) {
                    val freshLoc = result.lastLocation
                    stopActiveLocationUpdates()
                    cleanUpTimeout()
                    isLocating = false

                    if (isValidFreshLocation(freshLoc)) {
                        handleLocationSuccess(freshLoc!!)
                    } else {
                        handleLocationFailure("Unable to get your current location. Please try again.")
                    }
                }
            }
            activeLocationCallback = callback
            fusedLocationClient.requestLocationUpdates(locationRequest, callback, Looper.getMainLooper())
        } catch (e: Exception) {
            cleanUpTimeout()
            isLocating = false
            handleLocationFailure("Unable to get your current location: ${e.localizedMessage}")
        }
    }

    private fun stopActiveLocationUpdates() {
        activeCts?.cancel()
        activeCts = null
        activeLocationCallback?.let { cb ->
            try {
                fusedLocationClient.removeLocationUpdates(cb)
            } catch (_: Exception) {}
        }
        activeLocationCallback = null
    }

    private fun cleanUpTimeout() {
        locationTimeoutRunnable?.let { locationTimeoutHandler.removeCallbacks(it) }
        locationTimeoutRunnable = null
    }

    private fun isValidFreshLocation(loc: Location?): Boolean {
        if (loc == null) return false
        val lat = loc.latitude
        val lon = loc.longitude

        // Validate coordinate bounds
        if (lat < -90.0 || lat > 90.0 || lon < -180.0 || lon > 180.0) return false
        // Exclude Null Island (0.0, 0.0)
        if (lat == 0.0 && lon == 0.0) return false

        // Check freshness: reject locations older than 3 minutes (180,000 ms)
        val ageMs = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            (SystemClock.elapsedRealtimeNanos() - loc.elapsedRealtimeNanos) / 1_000_000L
        } else {
            System.currentTimeMillis() - loc.time
        }
        if (ageMs > MAX_LOCATION_AGE_MS || ageMs < -60 * 1000L) {
            return false
        }

        // Accuracy check: reject wild estimates (> 2000 meters)
        if (loc.hasAccuracy() && loc.accuracy > MAX_ACCEPTABLE_ACCURACY_METERS) {
            return false
        }

        return true
    }

    private fun handleLocationSuccess(location: Location) {
        currentLat = location.latitude
        currentLon = location.longitude

        txtLocation.text = String.format(Locale.US, "📍 Location: %.4f° N, %.4f° E", currentLat, currentLon)
        txtLocation.setTextColor(Color.parseColor("#34D399"))

        btnRetryLocation.visibility = View.GONE
        btnEnableGps.visibility = View.GONE

        val fineGranted = ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
        if (!fineGranted) {
            txtLocationWarning.text = "⚠️ Approximate location granted. Precise Location is recommended for accurate hyper-local pollution intelligence."
            txtLocationWarning.visibility = View.VISIBLE
        } else {
            txtLocationWarning.visibility = View.GONE
        }

        // Calculate location age
        val ageMs = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN_MR1) {
            (SystemClock.elapsedRealtimeNanos() - location.elapsedRealtimeNanos) / 1_000_000L
        } else {
            System.currentTimeMillis() - location.time
        }
        val ageSec = Math.max(0L, ageMs / 1000L)

        val timeStr = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US).format(Date(location.time))
        val providerStr = location.provider ?: "fused"
        val accuracyStr = if (location.hasAccuracy()) {
            val precisionLabel = when {
                location.accuracy <= 20f -> "High Precision GPS"
                location.accuracy <= 100f -> "Good Accuracy"
                else -> "Coarse Accuracy"
            }
            String.format(Locale.US, "±%.1f m (%s)", location.accuracy, precisionLabel)
        } else {
            "Accuracy not reported"
        }

        txtDebugCoords.text = String.format(Locale.US, "Coordinates: Lat %.6f, Lon %.6f", currentLat, currentLon)
        txtDebugAccuracy.text = "Accuracy: $accuracyStr"
        txtDebugTimestamp.text = "Timestamp: $timeStr (Age: ${ageSec}s)"
        txtDebugProvider.text = "Provider / Source: $providerStr (Google Play Services FusedLocationProviderClient)"

        // Persist fresh valid coordinates
        val prefs = getSharedPreferences("vayunet_prefs", Context.MODE_PRIVATE)
        prefs.edit()
            .putFloat("last_valid_lat", currentLat.toFloat())
            .putFloat("last_valid_lon", currentLon.toFloat())
            .putLong("last_valid_time", location.time)
            .putFloat("last_lat", currentLat.toFloat())
            .putFloat("last_lon", currentLon.toFloat())
            .apply()

        // Run pollution analysis strictly for the verified device coordinates
        runPollutionAnalysis(currentLat, currentLon)
    }

    private fun handleLocationFailure(reason: String) {
        currentLat = 0.0
        currentLon = 0.0

        txtLocation.text = "⚠️ Unable to get your current location. Please try again."
        txtLocation.setTextColor(Color.parseColor("#F87171"))

        txtLocationWarning.text = reason
        txtLocationWarning.visibility = View.VISIBLE
        btnRetryLocation.visibility = View.VISIBLE

        if (!isLocationServicesEnabled()) {
            btnEnableGps.visibility = View.VISIBLE
        } else {
            btnEnableGps.visibility = View.GONE
        }

        txtDebugCoords.text = "Coordinates: Unavailable (Halted)"
        txtDebugAccuracy.text = "Accuracy: —"
        txtDebugTimestamp.text = "Timestamp: Failed at ${SimpleDateFormat("HH:mm:ss", Locale.US).format(Date())}"
        txtDebugProvider.text = "Provider / Source: FusedLocationProviderClient (No fix)"

        statusView.text = "Location Unavailable"
        statusView.setTextColor(Color.parseColor("#F87171"))
        txtHotspot.text = "Pollution hotspot: Halted (requires valid location)"
        txtMovement.text = "Movement: Halted"
        txtAdvice.text = "Unable to get physical device location. Please enable GPS and tap 'Retry Location'."
        detailsView.text = "VayuNet never analyzes pollution for unverified locations."
    }

    private fun runPollutionAnalysis(lat: Double, lon: Double) {
        if (lat == 0.0 && lon == 0.0) return

        statusView.text = "Checking nearby pollution..."
        statusView.setTextColor(Color.parseColor("#99F6E4"))
        txtHotspot.text = "Pollution hotspot: Analyzing surrounding area..."
        txtMovement.text = "Movement: Calculating wind trajectory..."
        txtAdvice.text = "Advisory: Fetching Sentinel-5P satellite observations..."

        val baseUrl = getSavedBaseUrl()
        val apiUrl = "$baseUrl/api/analyze"

        CoroutineScope(Dispatchers.IO).launch {
            try {
                val jsonPayload = JSONObject().apply {
                    put("latitude", lat)
                    put("longitude", lon)
                }

                val url = URL(apiUrl)
                val conn = (url.openConnection() as HttpURLConnection).apply {
                    requestMethod = "POST"
                    setRequestProperty("Content-Type", "application/json")
                    setRequestProperty("Accept", "application/json")
                    doOutput = true
                    connectTimeout = 8000
                    readTimeout = 8000
                }

                OutputStreamWriter(conn.outputStream).use { it.write(jsonPayload.toString()) }

                if (conn.responseCode == 200) {
                    val response = BufferedReader(InputStreamReader(conn.inputStream)).use { it.readText() }
                    val data = JSONObject(response)

                    withContext(Dispatchers.Main) {
                        renderAnalysisResponse(data)
                    }
                } else {
                    withContext(Dispatchers.Main) {
                        statusView.text = "Server returned status ${conn.responseCode}"
                        detailsView.text = "Check if backend is running at $baseUrl"
                    }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) {
                    statusView.text = "Connection Offline"
                    statusView.setTextColor(Color.parseColor("#F87171"))
                    txtHotspot.text = "Could not reach backend at $baseUrl"
                    txtMovement.text = "Error: ${e.localizedMessage}"
                    txtAdvice.text = "Verify connection and ensure backend is running."
                }
            }
        }
    }

    private fun renderAnalysisResponse(data: JSONObject) {
        val risk = data.optString("risk_level", "LOW")
        val alertObj = data.optJSONObject("alert")
        val weatherObj = data.optJSONObject("weather")
        val movementObj = data.optJSONObject("movement")
        val hotspotObj = data.optJSONObject("pollution_hotspot")

        // 1. Status View
        when (risk.uppercase()) {
            "CRITICAL", "HIGH" -> {
                statusView.text = "🔴 HIGH POLLUTION RISK"
                statusView.setTextColor(Color.parseColor("#EF4444"))
            }
            "MODERATE" -> {
                statusView.text = "🟠 MODERATE POLLUTION"
                statusView.setTextColor(Color.parseColor("#F97316"))
            }
            "NEARBY_STABLE", "NEARBY" -> {
                statusView.text = "🟡 NEARBY POLLUTION DETECTED"
                statusView.setTextColor(Color.parseColor("#EAB308"))
            }
            else -> {
                statusView.text = "🟢 AIR CONDITIONS STABLE"
                statusView.setTextColor(Color.parseColor("#10B981"))
            }
        }

        // 2. Hotspot
        val hotspotDetected = hotspotObj?.optBoolean("detected", false) ?: false
        if (hotspotDetected) {
            val dist = hotspotObj?.optDouble("distance_km", 0.0) ?: 0.0
            val dir = hotspotObj?.optString("direction", "nearby") ?: "nearby"
            val pol = hotspotObj?.optString("pollutant", "NO2") ?: "NO2"
            txtHotspot.text = String.format(Locale.US, "🔴 Hotspot: %.1f km %s (%s elevated)", dist, dir, pol)
            txtHotspot.setTextColor(Color.parseColor("#F87171"))
        } else {
            val desc = hotspotObj?.optString("description", "No clear hotspot detected") ?: "No clear hotspot detected"
            txtHotspot.text = "🟢 Hotspot: $desc in surrounding radius"
            txtHotspot.setTextColor(Color.parseColor("#34D399"))
        }

        // 3. Movement
        val windSpeed = weatherObj?.optDouble("wind_speed_kmh", 0.0) ?: 0.0
        val windCompass = weatherObj?.optString("direction_compass", "Calm") ?: "Calm"
        val moveDir = movementObj?.optString("direction", windCompass) ?: windCompass
        txtMovement.text = String.format(Locale.US, "➡️ Wind: %s (%.0f km/h) • Possible movement: %s", windCompass, windSpeed, moveDir)

        // 4. Advisory
        val advisory = alertObj?.optString("message_en", "Air conditions look stable.") ?: "Air conditions look stable."
        txtAdvice.text = advisory

        // 5. Details
        val timeStr = SimpleDateFormat("h:mm a", Locale.getDefault()).format(Date())
        detailsView.text = "Updated: $timeStr • Analysis radius: 15 km"

        // 6. Update Home-Screen AppWidget
        val manager = AppWidgetManager.getInstance(this)
        val component = ComponentName(this, VayuWidgetProvider::class.java)
        val ids = manager.getAppWidgetIds(component)
        val windText = "Wind: $windCompass"
        for (id in ids) {
            VayuWidgetProvider.updateAppWidget(this, manager, id, risk, advisory, windText, timeStr)
        }

        // 7. Fire native notification if high risk
        if (risk.equals("HIGH", ignoreCase = true) || risk.equals("CRITICAL", ignoreCase = true)) {
            NotificationHelper.showRiskNotification(this, risk, advisory, moveDir)
        }
    }
}
