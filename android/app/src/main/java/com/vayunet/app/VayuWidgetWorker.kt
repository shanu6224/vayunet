package com.vayunet.app

import android.appwidget.AppWidgetManager
import android.content.ComponentName
import android.content.Context
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.google.android.gms.tasks.CancellationTokenSource
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withTimeoutOrNull
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class VayuWidgetWorker(
    private val context: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(context, workerParams) {

    override suspend fun doWork(): Result {
        return try {
            val prefs = context.getSharedPreferences("vayunet_prefs", Context.MODE_PRIVATE)
            val baseUrl = prefs.getString("api_base_url", AppConfig.DEFAULT_API_BASE_URL)?.trimEnd('/') ?: AppConfig.DEFAULT_API_BASE_URL

            var lat = 0.0
            var lon = 0.0

            // 1. Try to obtain a fresh device location via Google Play Services FusedLocationProviderClient
            val fineGranted = ContextCompat.checkSelfPermission(context, android.Manifest.permission.ACCESS_FINE_LOCATION) == PackageManager.PERMISSION_GRANTED
            val coarseGranted = ContextCompat.checkSelfPermission(context, android.Manifest.permission.ACCESS_COARSE_LOCATION) == PackageManager.PERMISSION_GRANTED

            if (fineGranted || coarseGranted) {
                try {
                    val fusedClient = LocationServices.getFusedLocationProviderClient(context)
                    val priority = if (fineGranted) Priority.PRIORITY_BALANCED_POWER_ACCURACY else Priority.PRIORITY_LOW_POWER
                    val cts = CancellationTokenSource()
                    val freshLoc = withTimeoutOrNull(5000L) {
                        fusedClient.getCurrentLocation(priority, cts.token).await()
                    }

                    if (isValidLocation(freshLoc)) {
                        lat = freshLoc!!.latitude
                        lon = freshLoc.longitude
                        prefs.edit()
                            .putFloat("last_valid_lat", lat.toFloat())
                            .putFloat("last_valid_lon", lon.toFloat())
                            .putLong("last_valid_time", freshLoc.time)
                            .apply()
                    }
                } catch (_: Exception) {}
            }

            // 2. If fresh location was not acquired, check stored last valid coordinates
            if (lat == 0.0 && lon == 0.0) {
                val storedLat = prefs.getFloat("last_valid_lat", 0.0f).toDouble()
                val storedLon = prefs.getFloat("last_valid_lon", 0.0f).toDouble()

                // Strictly validate stored coordinates: must be within valid bounds, not 0,0, and NEVER Chennai or other fallback
                if (storedLat in -90.0..90.0 && storedLon in -180.0..180.0 &&
                    !(storedLat == 0.0 && storedLon == 0.0) &&
                    !(storedLat == 13.0827 && storedLon == 80.2707)) {
                    lat = storedLat
                    lon = storedLon
                }
            }

            // 3. If NO valid location is available, show "Location unavailable" and DO NOT analyze a wrong location
            if (lat == 0.0 && lon == 0.0) {
                renderWidgetLocationUnavailable()
                return Result.success()
            }

            val apiUrl = "$baseUrl/api/analyze"
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

                val statusCard = data.optJSONObject("status_card")
                val statusTitle = statusCard?.optString("title_en")
                val risk = data.optString("risk_level", "LOW")
                val displayRisk = statusTitle ?: risk

                val alertObj = data.optJSONObject("alert")
                val weatherObj = data.optJSONObject("weather")
                val movementObj = data.optJSONObject("movement")

                val message = alertObj?.optString("message_en") 
                    ?: statusCard?.optString("summary_en")
                    ?: (if (risk == "HIGH" || risk == "CRITICAL") "Pollution may move toward you." else "Air conditions look stable.")
                val windCompass = weatherObj?.optString("direction_compass", "SE") ?: "SE"
                val windSpeed = weatherObj?.optDouble("wind_speed_kmh", 0.0) ?: 0.0
                val windText = if (windSpeed > 0) "Wind: $windCompass (${windSpeed.toInt()} km/h)" else "Wind: $windCompass"
                val movementDir = movementObj?.optString("direction", windCompass) ?: windCompass
                val timeStr = SimpleDateFormat("h:mm a", Locale.getDefault()).format(Date())

                // Update Widgets
                val manager = AppWidgetManager.getInstance(context)
                val component = ComponentName(context, VayuWidgetProvider::class.java)
                val ids = manager.getAppWidgetIds(component)

                for (id in ids) {
                    VayuWidgetProvider.updateAppWidget(
                        context,
                        manager,
                        id,
                        displayRisk,
                        message,
                        windText,
                        timeStr
                    )
                }

                // If high risk, trigger native notification with sound and vibration
                if (risk.equals("HIGH", ignoreCase = true) || risk.equals("CRITICAL", ignoreCase = true)) {
                    NotificationHelper.showRiskNotification(context, risk, message, movementDir)
                }

                Result.success()
            } else {
                Result.retry()
            }
        } catch (e: Exception) {
            renderWidgetLocationUnavailable()
            Result.success()
        }
    }

    private fun isValidLocation(loc: android.location.Location?): Boolean {
        if (loc == null) return false
        val lat = loc.latitude
        val lon = loc.longitude
        if (lat < -90.0 || lat > 90.0 || lon < -180.0 || lon > 180.0) return false
        if (lat == 0.0 && lon == 0.0) return false
        if (lat == 13.0827 && lon == 80.2707) return false
        return true
    }

    private fun renderWidgetLocationUnavailable() {
        val timeStr = SimpleDateFormat("h:mm a", Locale.getDefault()).format(Date())
        val manager = AppWidgetManager.getInstance(context)
        val component = ComponentName(context, VayuWidgetProvider::class.java)
        val ids = manager.getAppWidgetIds(component)
        for (id in ids) {
            VayuWidgetProvider.updateAppWidget(
                context,
                manager,
                id,
                "LOCATION UNAVAILABLE",
                "Location unavailable. Open app to acquire GPS.",
                "Wind: --",
                timeStr
            )
        }
    }
}
