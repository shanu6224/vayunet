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
import android.location.LocationListener
import android.location.LocationManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
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

class MainActivity : Activity(), LocationListener {

    private lateinit var editApiUrl: EditText
    private lateinit var txtLocation: TextView
    private lateinit var statusView: TextView
    private lateinit var txtHotspot: TextView
    private lateinit var txtMovement: TextView
    private lateinit var txtAdvice: TextView
    private lateinit var detailsView: TextView

    private var currentLat: Double = 0.0
    private var currentLon: Double = 0.0
    private lateinit var locationManager: LocationManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Initialize Native Notification Channel
        NotificationHelper.createNotificationChannel(this)

        // Bind Views
        editApiUrl = findViewById(R.id.editApiUrl)
        val btnSaveApi = findViewById<Button>(R.id.btnSaveApi)
        val btnCheckLocation = findViewById<Button>(R.id.btnCheckLocation)
        txtLocation = findViewById(R.id.txtLocation)
        statusView = findViewById(R.id.status)
        txtHotspot = findViewById(R.id.txtHotspot)
        txtMovement = findViewById(R.id.txtMovement)
        txtAdvice = findViewById(R.id.txtAdvice)
        detailsView = findViewById(R.id.details)
        val btnOpenPwa = findViewById<Button>(R.id.btnOpenPwa)
        val btnTestAlert = findViewById<Button>(R.id.btnTestAlert)
        val btnUpdateWidget = findViewById<Button>(R.id.btnUpdateWidget)

        // Load saved preferences
        val prefs = getSharedPreferences("vayunet_prefs", Context.MODE_PRIVATE)
        val savedApiUrl = prefs.getString("api_base_url", AppConfig.DEFAULT_API_BASE_URL) ?: AppConfig.DEFAULT_API_BASE_URL
        editApiUrl.setText(savedApiUrl)
        currentLat = prefs.getFloat("last_lat", 0.0f).toDouble()
        currentLon = prefs.getFloat("last_lon", 0.0f).toDouble()
        if (currentLat != 0.0 && currentLon != 0.0) {
            txtLocation.text = String.format(Locale.US, "📍 Location: %.4f° N, %.4f° E", currentLat, currentLon)
        } else {
            txtLocation.text = "📍 Location: Acquiring GPS device coordinates..."
        }

        locationManager = getSystemService(Context.LOCATION_SERVICE) as LocationManager

        // Request Permissions
        checkAndRequestPermissions()

        // Save API URL
        btnSaveApi.setOnClickListener {
            val url = editApiUrl.text.toString().trim()
            if (url.isNotEmpty()) {
                prefs.edit().putString("api_base_url", url).apply()
                Toast.makeText(this, "API Base URL saved: $url", Toast.LENGTH_SHORT).show()
            }
        }

        // Check Location & Trigger Analysis
        btnCheckLocation.setOnClickListener {
            acquireLocationAndAnalyze()
        }

        // Open PWA in browser
        btnOpenPwa.setOnClickListener {
            val baseUrl = getSavedBaseUrl()
            val pwaUrl = if (baseUrl.contains(":8000")) {
                baseUrl.replace(":8000", ":5173")
            } else if (baseUrl.contains("vayunet-api.onrender.com")) {
                baseUrl.replace("vayunet-api.onrender.com", "vayunet-app.onrender.com")
            } else if (baseUrl.startsWith("http")) {
                AppConfig.DEFAULT_PWA_URL
            } else {
                AppConfig.DEFAULT_PWA_URL
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
            NotificationHelper.showRiskNotification(
                this,
                "HIGH",
                "Pollution may move toward your area.",
                "South-East"
            )
            Toast.makeText(this, "Fired native alert with sound & vibration.", Toast.LENGTH_SHORT).show()
        }

        // Trigger Immediate Widget Update
        btnUpdateWidget.setOnClickListener {
            val workRequest = OneTimeWorkRequestBuilder<VayuWidgetWorker>().build()
            WorkManager.getInstance(this).enqueue(workRequest)
            Toast.makeText(this, "Widget background sync queued.", Toast.LENGTH_SHORT).show()
        }

        // Run initial check
        acquireLocationAndAnalyze()
    }

    private fun getSavedBaseUrl(): String {
        val prefs = getSharedPreferences("vayunet_prefs", Context.MODE_PRIVATE)
        return prefs.getString("api_base_url", AppConfig.DEFAULT_API_BASE_URL)?.trimEnd('/') ?: AppConfig.DEFAULT_API_BASE_URL
    }

    private fun acquireLocationAndAnalyze() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED ||
            ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED) {

            val lastGps = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER)
            val lastNet = locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
            val bestLocation = lastGps ?: lastNet

            if (bestLocation != null) {
                currentLat = bestLocation.latitude
                currentLon = bestLocation.longitude
                onLocationChanged(bestLocation)
            } else {
                try {
                    locationManager.requestSingleUpdate(LocationManager.NETWORK_PROVIDER, this, null)
                } catch (e: Exception) {
                    // Fall back to stored coordinates
                }
            }
        }

        // Run pollution analysis for current coordinates
        runPollutionAnalysis(currentLat, currentLon)
    }

    private fun runPollutionAnalysis(lat: Double, lon: Double) {
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
                    txtAdvice.text = "Verify Wi-Fi IP and ensure backend is running."
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

    override fun onLocationChanged(location: Location) {
        currentLat = location.latitude
        currentLon = location.longitude
        txtLocation.text = String.format(Locale.US, "📍 Location: %.4f° N, %.4f° E", currentLat, currentLon)
        val prefs = getSharedPreferences("vayunet_prefs", Context.MODE_PRIVATE)
        prefs.edit()
            .putFloat("last_lat", currentLat.toFloat())
            .putFloat("last_lon", currentLon.toFloat())
            .apply()
    }

    private fun checkAndRequestPermissions() {
        val permissionsToRequest = mutableListOf<String>()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
            != PackageManager.PERMISSION_GRANTED) {
            permissionsToRequest.add(Manifest.permission.ACCESS_FINE_LOCATION)
            permissionsToRequest.add(Manifest.permission.ACCESS_COARSE_LOCATION)
        }

        if (permissionsToRequest.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, permissionsToRequest.toTypedArray(), 101)
        }
    }
}
