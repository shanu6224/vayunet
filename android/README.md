# Native Android widget

This is the real home-screen widget layer.

Open the `android` folder in Android Studio.

The widget is a native Android AppWidgetProvider, so it can be placed on the phone
home screen. Android controls the periodic update schedule. For event-driven alerts,
use FCM/local notifications rather than trying to keep a widget continuously running.

For remote alerts:
1. Create Firebase project.
2. Add Android app package `com.vayunet.app`.
3. Put `google-services.json` in `android/app/`.
4. Add the Firebase plugin/dependency.
5. Implement FirebaseMessagingService and connect the backend token.
