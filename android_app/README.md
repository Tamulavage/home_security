# Android Security Viewer App

This native Android app connects to the Raspberry Pi Flask server to display:

- current temperature and humidity
- motion detection status
- live MJPEG video feed

## Setup

1. Open this project in Android Studio.
2. Configure the Pi host and API key in the app UI.
3. Build and run on a device.

## Notes

- The app currently uses `X-API-KEY` in requests to authenticate with the Pi server.
- Use the app to view the MJPEG camera stream and monitor motion status.
