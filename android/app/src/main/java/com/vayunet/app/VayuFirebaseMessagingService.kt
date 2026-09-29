package com.vayunet.app

import android.util.Log
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager

/**
 * VayuNet Firebase Cloud Messaging receiver for remote alert architecture.
 *
 * Flow:
 * Backend Event Detected -> Firebase Cloud Messaging -> Phone -> Notification with Sound/Vibration -> Widget Refresh
 *
 * Setup:
 * 1. Add google-services.json to android/app/
 * 2. In android/build.gradle: id 'com.google.gms.google-services' version '4.4.2' apply false
 * 3. In android/app/build.gradle: id 'com.google.gms.google-services', implementation 'com.google.firebase:firebase-messaging-ktx:24.1.0'
 * 4. Register VayuFirebaseMessagingService in AndroidManifest.xml.
 */
class VayuFirebaseMessagingService {
    companion object {
        private const val TAG = "VayuNetFCM"

        /**
         * Called when a push alert is received from Firebase or local simulator.
         */
        fun handlePushPayload(
            context: android.content.Context,
            data: Map<String, String>
        ) {
            val riskLevel = data["risk_level"] ?: "HIGH"
            val message = data["message"] ?: "Elevated pollution risk signal detected near your coordinates."
            val movement = data["movement"] ?: "downwind"

            Log.i(TAG, "Push event received: Risk=$riskLevel, Movement=$movement")

            // 1. Show native notification with sound and vibration
            NotificationHelper.showRiskNotification(
                context,
                riskLevel,
                message,
                movement
            )

            // 2. Trigger immediate widget refresh
            val work = OneTimeWorkRequestBuilder<VayuWidgetWorker>().build()
            WorkManager.getInstance(context).enqueue(work)
        }
    }
}
