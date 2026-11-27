# Home Security

Home Security is a multi-platform monitoring system that combines a Raspberry Pi
Flask server with a desktop dashboard and an Android viewer.

The Pi exposes sensor data, camera controls, and an MJPEG video stream. The
desktop and Android clients connect to that server to display status and control
the camera and motion-triggered recordings.

## Components

| Component | Description |
| --- | --- |
| [Pi server](pi_server/README.md) | Flask API, DHT11/PIR sensors, camera streaming and motion recordings |
| [Desktop dashboard](ui_dashboard/README.md) | PyQt5 application for monitoring and controls |
| [Android viewer](android_app/README.md) | Native Android application for monitoring the system |

## System overview

```text
Sensors and camera
       |
       v
Raspberry Pi Flask server (:5000)
       |
       +---- PyQt5 desktop dashboard
       |
       +---- Android application
```

The server reports temperature and humidity, motion state, camera state,
recording state, and live video. Desktop and Android clients authenticate API
requests with the same shared key.

## Prerequisites

- Raspberry Pi OS with Python 3 and the required GPIO/camera hardware
- Python 3 for the desktop dashboard
- Android Studio or another Android build environment for the mobile app
- A shared network between the Pi and client devices

## Security configuration

Set a strong API key before starting the Pi server:

**Linux/Pi or macOS**

```bash
export PI_SERVER_API_KEY="replace-with-a-long-random-secret"
export FLASK_HOST="0.0.0.0"
export FLASK_PORT="5000"
```

**Windows PowerShell**

```powershell
$env:PI_SERVER_API_KEY = "replace-with-a-long-random-secret"
$env:FLASK_HOST = "0.0.0.0"
$env:FLASK_PORT = "5000"
```

The default key is intentionally invalid; the server refuses to start unless
`PI_SERVER_API_KEY` is set to another value.

Optional Pi server settings include:

| Variable | Default | Purpose |
| --- | --- | --- |
| `DHT_PIN` | `5` | DHT11 GPIO data pin |
| `PIR_PIN` | `17` | PIR sensor GPIO pin |
| `CAMERA_FPS` | `24` | Camera capture frame rate |
| `SENSOR_READ_INTERVAL_SECONDS` | `5` | Sensor polling interval |
| `MOTION_RESET_SECONDS` | `10` | Motion clear timeout |
| `RECORDINGS_DIR` | `pi_server/recordings` | H.264 motion recording directory |
| `FCM_SERVER_KEY` | empty | Firebase server key for push notifications |

Clients authenticate by sending `X-API-KEY` with the shared key. The Pi API also
accepts `api_key` as a query parameter, but the header form is preferred because
it avoids exposing the secret in URLs and logs.

## Quick start

### 1. Start the Pi server

On the Raspberry Pi:

```bash
python3 -m venv --system-site-packages env
source env/bin/activate
python3 -m pip install -r pi_server/requirements.txt

export PI_SERVER_API_KEY="replace-with-a-long-random-secret"
python3 pi_server/app.py
```

The server listens on `0.0.0.0:5000` by default. Check it from a browser or
command line at `http://<pi-address>:5000/health`; protected endpoints still
require the API key.

### 2. Start the desktop dashboard

From the repository root:

```powershell
python -m venv env
env\Scripts\activate
python -m pip install -r ui_dashboard/requirements.txt
python -m ui_dashboard.main
```

In the dashboard settings, enter:

- Server URL: `http://<pi-address>:5000`
- API key: the value of `PI_SERVER_API_KEY`

The desktop configuration is stored under `~/.ui_dashboard/.env` on Windows,
Linux, and macOS.

### 3. Build the Android viewer

On Windows, from the repository root:

```powershell
cd android_app
.\gradlew.bat assembleDebug
```

Open the app and configure it with the Pi host address and the same API key.
The Android app assumes port `5000`.

For development in Android Studio, open the `android_app` directory and run the
app module on a device or emulator that can reach the Pi.

## API summary

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Server availability |
| `GET` | `/status` | Sensor, camera, motion, and recording status |
| `GET` | `/temperature` | Temperature and humidity |
| `GET` | `/motion` | Motion state |
| `GET` | `/video_feed` | MJPEG camera stream |
| `POST` | `/camera/start` | Enable the camera |
| `POST` | `/camera/stop` | Disable the camera |
| `POST` | `/recording/disable` | Disable recording or suppress the active motion period |
| `POST` | `/recording/enable` | Re-enable recording |
| `POST` | `/register_device` | Register a device for notifications |

See [pi_server/README.md](pi_server/README.md) for recording behavior and
authentication details.

## Development

Repository-level component instructions are available in [AGENTS.md](AGENTS.md).
Component-specific run and test guidance lives in the three component README
files.

There is no centralized test runner or CI configuration in the repository.
Validate changes with component-specific commands:

- Pi server: run the Flask app and exercise the API with its API key
- Camera: run `python pi_server/test_camera.py`
- Desktop: start `python -m ui_dashboard.main`
- Android: run `android_app/gradlew.bat assembleDebug` on Windows

## Repository layout

```text
pi_server/       Flask API, sensors, camera, recording, and notifications
ui_dashboard/    PyQt5 desktop application
android_app/     Native Android viewer
README.md        Project overview
AGENTS.md        Repository guidance for coding agents
```
