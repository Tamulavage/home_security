# Agent: android_app

Purpose
- Provide quick build/run instructions and important conventions for the native Android app.

Quick build (Windows)
```powershell
cd android_app
.\gradlew.bat assembleDebug
```

Recommended development workflow
- Open `android_app` in Android Studio for iterative builds and debugging.
- Use the Gradle wrapper (`gradlew` / `gradlew.bat`) — do not change Gradle settings globally.

Configuration and notes
- API auth: App uses `X-API-KEY` header; configure server URL/API key in the app UI or build-time config if present.
- local.properties may contain SDK path — do not check in sensitive local settings.

Quick smoke tests
- Build APK: `.\uild\outputs\apk\debug\app-debug.apk`
- Verify network calls from device/emulator to Pi server and ensure API key is accepted.

Important files
- `android_app/app/src/main/` — app source and resources
- `android_app/build.gradle.kts` and `android_app/app/build.gradle.kts` — build config

Agent hints
- Avoid editing global Gradle or SDK configs; restrict changes to module-level build files and ask before major changes.
- Link to [android_app/README.md](android_app/README.md) for feature overview.
