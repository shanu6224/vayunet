package com.vayunet.app

import android.appwidget.AppWidgetManager
import android.content.ComponentName
import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
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
            val lat = prefs.getFloat("last_lat", 0.0f).toDouble()
            val lon = prefs.getFloat("last_lon", 0.0f).toDouble()

            // If coordinates not yet recorded, skip sync until location is acquired
            if (lat == 0.0 && lon == 0.0) {
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

                val risk = data.optString("risk_level", "LOW")
                val alertObj = data.optJSONObject("alert")
                val weatherObj = data.optJSONObject("weather")
                val movementObj = data.optJSONObject("movement")

                val message = alertObj?.optString("message_en") 
                    ?: (if (risk == "HIGH" || risk == "CRITICAL") "Pollution may move toward you." else "Air conditions look stable.")
                val windCompass = weatherObj?.optString("direction_compass", "SE") ?: "SE"
                val windText = "Wind: $windCompass"
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
                        risk,
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
            // Fallback: update widget with offline state
            val timeStr = SimpleDateFormat("h:mm a", Locale.getDefault()).format(Date())
            val manager = AppWidgetManager.getInstance(context)
            val component = ComponentName(context, VayuWidgetProvider::class.java)
            val ids = manager.getAppWidgetIds(component)
            for (id in ids) {
                VayuWidgetProvider.updateAppWidget(
                    context,
                    manager,
                    id,
                    "LOW",
                    "Checking nearby pollution...",
                    "Wind: --",
                    timeStr
                )
            }
            Result.success()
        }
    }
}
