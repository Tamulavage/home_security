# Agent: ui_dashboard

Purpose
- Short, actionable guidance for running and testing the PyQt5 dashboard locally.

Quick run (desktop)
```bash
pip install -r ui_dashboard/requirements.txt
python -m ui_dashboard.main
```

Configuration
- Config loaded from `~/.security_dashboard/.env` (Windows: `C:\Users\<user>\.security_dashboard\.env`) or environment variables:
  - `SECURITY_SERVER_URL` — Pi server base URL
  - `SECURITY_API_KEY` — API key matching `PI_SERVER_API_KEY`

Smoke tests
- Verify connection: open app and use Settings → Connect.
- CLI: `curl -H "X-API-KEY: $SECURITY_API_KEY" http://<pi>:5000/status`

Important files
- `ui_dashboard/api_client.py` — REST client and MJPEG parsing
- `ui_dashboard/config.py` — config load/save and validation
- `ui_dashboard/main.py` — entrypoint

Common issues
- Missing PyQt5 or Pillow: ensure `requirements.txt` installed in same Python interpreter used to run GUI.
- MJPEG parsing errors: check camera is enabled on the Pi and `video_feed` is reachable.

Example code
```python
from ui_dashboard.api_client import SecurityAppClient

client = SecurityAppClient(
    server_url="http://192.168.1.100:5000",
    api_key="your-api-key",
    timeout=5.0,
)

status = client.get_status()
print(status["temperature_c"], status["humidity"], status["motion_detected"])

# stream video in the same style used in the dashboard
for chunk in client.get_video_stream():
    # pass frames to the MJPEG widget
    print(type(chunk).__name__)
```

Agent hints
- Prefer changing UI behavior in small, testable increments.
- Avoid bundling large test data; use live endpoints or small mocks.
- Link back to [ui_dashboard/README.md](ui_dashboard/README.md) for full docs.
