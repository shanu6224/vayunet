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
        for (id in ids) {
            updateAppWidget(
                context,
                manager,
                id,
                "LOW",
                "Air conditions look stable.",
                "Wind: Calm",
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

            val (statusText, statusColor) = when (riskLevel.uppercase()) {
                "CRITICAL", "HIGH" -> Pair("🔴 HIGH RISK", Color.parseColor("#EF4444"))
                "MODERATE" -> Pair("🟠 MODERATE RISK", Color.parseColor("#F97316"))
                "NEARBY_STABLE", "NEARBY" -> Pair("🟡 NEARBY DETECTED", Color.parseColor("#EAB308"))
                "LOW" -> Pair("🟢 AIR GOOD", Color.parseColor("#10B981"))
                else -> Pair("🟢 AIR GOOD", Color.parseColor("#10B981"))
            }

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
