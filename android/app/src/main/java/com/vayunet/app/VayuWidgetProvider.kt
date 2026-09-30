package com.vayunet.app

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.os.Build
import android.widget.RemoteViews
import androidx.work.*
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.TimeUnit

class VayuWidgetProvider : AppWidgetProvider() {

    override fun onUpdate(context: Context, manager: AppWidgetManager, ids: IntArray) {
        val timeStr = SimpleDateFormat("h:mm a", Locale.getDefault()).format(Date())
        val prefs = context.getSharedPreferences("vayunet_prefs", Context.MODE_PRIVATE)
        val lastLat = prefs.getFloat("last_valid_lat", 0f).toDouble()
        val lastLon = prefs.getFloat("last_valid_lon", 0f).toDouble()

        val hasValidLoc = (lastLat in -90.0..90.0 && lastLon in -180.0..180.0 &&
                !(lastLat == 0.0 && lastLon == 0.0) &&
                !(lastLat == 13.0827 && lastLon == 80.2707))

        val initialStatus = if (hasValidLoc) "SYNCING" else "LOCATION UNAVAILABLE"
        val initialMsg = if (hasValidLoc) "Syncing local air data..." else "Location unavailable. Open app to acquire GPS."

        for (id in ids) {
            updateAppWidget(
                context,
                manager,
                id,
                initialStatus,
                initialMsg,
                "Wind: --",
                timeStr
            )
        }

        // Trigger immediate background refresh
        val workRequest = OneTimeWorkRequestBuilder<VayuWidgetWorker>().build()
        WorkManager.getInstance(context).enqueue(workRequest)
    }

    override fun onEnabled(context: Context) {
        super.onEnabled(context)
        NotificationHelper.createNotificationChannel(context)

        // Schedule periodic widget updates every 30 minutes
        val periodicWork = PeriodicWorkRequestBuilder<VayuWidgetWorker>(
            30, TimeUnit.MINUTES,
            10, TimeUnit.MINUTES
        ).setConstraints(
            Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()
        ).build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            "VayuWidgetSync",
            ExistingPeriodicWorkPolicy.KEEP,
            periodicWork
        )
    }

    override fun onDisabled(context: Context) {
        super.onDisabled(context)
        WorkManager.getInstance(context).cancelUniqueWork("VayuWidgetSync")
    }

    companion object {
        fun updateAppWidget(
            context: Context,
            manager: AppWidgetManager,
            widgetId: Int,
            riskLevel: String,
            message: String,
            windText: String,
            timeText: String
        ) {
            val views = RemoteViews(context.packageName, R.layout.vayunet_widget)

            val (statusText, statusColor, bgRes) = when (riskLevel.uppercase().trim()) {
                "CRITICAL", "HIGH", "ATTENTION" -> Triple(
                    "🔴 ATTENTION",
                    Color.parseColor("#EF4444"),
                    R.drawable.widget_bg_alert
                )
                "MODERATE", "BE CAREFUL", "MEDIUM" -> Triple(
                    "🟠 BE CAREFUL",
                    Color.parseColor("#F59E0B"),
                    R.drawable.widget_bg_warning
                )
                "NEARBY_STABLE", "NEARBY", "POLLUTION NEARBY" -> Triple(
                    "🟡 POLLUTION NEARBY",
                    Color.parseColor("#EAB308"),
                    R.drawable.widget_bg_warning
                )
                "LOW", "AIR IS GOOD" -> Triple(
                    "🟢 AIR IS GOOD",
                    Color.parseColor("#10B981"),
                    R.drawable.widget_bg_safe
                )
                "LOCATION UNAVAILABLE", "LOCATION_UNAVAILABLE", "UNAVAILABLE" -> Triple(
                    "⚠️ NO LOCATION",
                    Color.parseColor("#94A3B8"),
                    R.drawable.widget_bg_safe
                )
                "SYNCING", "UPDATING" -> Triple(
                    "🔄 UPDATING",
                    Color.parseColor("#38BDF8"),
                    R.drawable.widget_bg_safe
                )
                else -> Triple(
                    "🟢 AIR IS GOOD",
                    Color.parseColor("#10B981"),
                    R.drawable.widget_bg_safe
                )
            }

            views.setInt(R.id.widgetRoot, "setBackgroundResource", bgRes)
            views.setTextViewText(R.id.widgetTitle, "VayuNet")
            views.setTextViewText(R.id.widgetStatus, statusText)
            views.setTextColor(R.id.widgetStatus, statusColor)
            views.setTextViewText(R.id.widgetMessage, message)
            views.setTextViewText(R.id.widgetWind, windText)
            views.setTextViewText(R.id.widgetTime, "Updated: $timeText")

            // Tap widget to launch main activity
            val intent = Intent(context, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
            val pendingIntent = PendingIntent.getActivity(
                context,
                widgetId,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) PendingIntent.FLAG_IMMUTABLE else 0)
            )
            views.setOnClickPendingIntent(R.id.widgetRoot, pendingIntent)

            manager.updateAppWidget(widgetId, views)
        }
    }
}
