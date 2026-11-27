# Raspberry Pi Security Server

This Flask server runs on a Raspberry Pi Zero 2 and exposes secure endpoints for:

- DHT11 temperature and humidity
- PIR motion detection
- onboard camera MJPEG video streaming
- device registration for Firebase Cloud Messaging alerts

## Setup

1. Install Python dependencies:
   sudo apt install python3 python3-pip python3-venv -y

   mkdir ~/Security
   cd ~/Security
   #python3 -m venv env
   python3 -m venv --system-site-packages env
   source env/bin/activate

   python3 -m pip install adafruit-circuitpython-dht lgpio RPi.GPIO Flask  picamera2

   sudo apt install python3-requests


2. Set required environment variables:

   - `PI_SERVER_API_KEY` - strong secret for API authentication
   - `FCM_SERVER_KEY` - Firebase server key for push notifications
   - `DHT_PIN` - GPIO pin for DHT11 data line (default `5`)
   - `PIR_PIN` - GPIO pin for PIR motion sensor (default `17`)

3. Run the server:

   python app.py

## API Endpoints

- `POST /register_device` - register a mobile device to receive motion alerts
- `GET /status` - current temperature, humidity, and motion state
- `GET /temperature` - current temperature and humidity
- `GET /motion` - current motion state
- `GET /video_feed` - MJPEG camera stream
- `POST /recording/disable` - disable motion-triggered recordings until re-enabled
- `POST /recording/enable` - re-enable motion-triggered recordings

### Authentication

All endpoints require either the `X-API-KEY` header or `api_key` query parameter matching `PI_SERVER_API_KEY`.

### Motion recordings

Each motion event creates a new `.h264` file in `pi_server/recordings/`. Set
`RECORDINGS_DIR` to change the output directory. Recordings stop when motion
clears. The MJPEG feed continues while recording: Picamera2 encodes the camera
stream from a half-resolution secondary stream, while H.264 recording uses the
full-resolution main stream. The live preview encodes every other camera frame
to reduce load on the Pi.

To disable recording triggers until re-enabled, send an empty JSON payload:

```json
{}
```

An authenticated request with no JSON body also disables recording. Use
`POST /recording/enable` to re-enable it.

To stop and suppress the recording for the currently active motion, send:

```json
{"during_current_motion": true}
```

Both disable options must be authenticated. The current-motion option returns `409`
when there is no active motion. The permanent disable remains active until
`POST /recording/enable`.

The `GET /status` response reports `recording_in_progress` (also available as
`recording_active`), `recording_paused`,
`recording_disabled`, `recording_paused_until_motion_clears`, and
`recording_disabled_remaining_seconds`. The current-motion pause remains active
while motion is detected and automatically clears only after the motion status
changes from detected to clear.

## Notes

- `video_feed` returns an MJPEG stream.
- The server persists registered devices in `devices.json`.
- If `FCM_SERVER_KEY` is configured, motion events trigger push notifications to registered devices.
