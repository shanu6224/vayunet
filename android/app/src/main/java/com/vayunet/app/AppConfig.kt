package com.vayunet.app

/**
 * Global application configuration for VayuNet.
 * Centralizes the public HTTPS backend URL for both MainActivity and VayuWidgetWorker.
 */
object AppConfig {
    /**
     * Default public HTTPS backend URL.
     * Replace with your deployed backend URL on Render, Railway, etc.
     * Example: "https://vayunet-api.onrender.com"
     */
    const val DEFAULT_API_BASE_URL: String = "https://vayunet-api.onrender.com"
    const val DEFAULT_PWA_URL: String = "https://vayunet-app.onrender.com"
}
