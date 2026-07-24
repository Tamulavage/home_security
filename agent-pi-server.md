# Agent: pi_server

Purpose
- Provide concise, actionable run/test/debug steps and important environment/config notes for the Raspberry Pi Flask server.

Quick run (Raspberry Pi / Linux)
```bash
python3 -m venv env
source env/bin/activate
python3 -m pip install -r pi_server/requirements.txt
python3 pi_server/app.py
```

Required environment variables
- `PI_SERVER_API_KEY` — API secret used by the server and clients.
- `FCM_SERVER_KEY` — Firebase server key (optional) for push notifications.
- `DHT_PIN` — GPIO pin for DHT11 (default 5).
- `PIR_PIN` — GPIO pin for PIR sensor (default 17).

Quick smoke tests
- Health: `curl http://<pi>:5000/health`
- Status: `curl -H "X-API-KEY: $PI_SERVER_API_KEY" http://<pi>:5000/status`
- Video feed (MJPEG): open `http://<pi>:5000/video_feed` in a browser

Important files to inspect
- `pi_server/app.py` — API endpoints and entrypoint
- `pi_server/config.py` — environment-driven configuration
- `pi_server/devices.json` — persisted device registrations

Common troubleshooting
- Missing GPIO libs: ensure Raspberry Pi has required packages and permissions.
- Camera issues: verify camera is enabled and picamera2 is installed.
- API auth errors: check `PI_SERVER_API_KEY` and header name `X-API-KEY`.

Agent hints
- Preserve README content: link to [pi_server/README.md](pi_server/README.md) rather than copying large sections.
- Do not attempt to modify hardware-specific defaults without asking.
- Use the smoke tests above before making behavioral changes.
