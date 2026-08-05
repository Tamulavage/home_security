# Copilot Instructions — Security Repo (root)

Quick guidance for AI coding agents working in this repository.

What this repo contains
- `pi_server/` — Flask-based Raspberry Pi server (see pi_server/README.md).
- `ui_dashboard/` — PyQt5 desktop dashboard (see ui_dashboard/README.md).
- `android_app/` — Native Android app; builds with Gradle wrapper (see android_app/README.md).

Quick commands
- Android (use Gradle wrapper in `android_app`):
  - Windows (from repo root): `cd android_app && .\gradlew.bat assembleDebug`
  - Recommended: open `android_app` in Android Studio for run/debug.
- Pi server (Raspberry Pi):
  ```bash
  python3 -m venv env
  source env/bin/activate
  python3 -m pip install -r pi_server/requirements.txt
  python3 pi_server/app.py
  ```
- UI Dashboard (desktop):
  ```bash
  pip install -r ui_dashboard/requirements.txt
  python -m ui_dashboard.main
  ```

Key files & components
- `pi_server/app.py` — Flask entrypoint and API endpoints. See [pi_server/README.md](pi_server/README.md).
- `pi_server/config.py` — environment-driven configuration and API key usage.
- `ui_dashboard/main.py` and `ui_dashboard/api_client.py` — desktop app entry and REST client. See [ui_dashboard/README.md](ui_dashboard/README.md).
- `android_app/` — Android app; uses `X-API-KEY` for auth. See [android_app/README.md](android_app/README.md).

Conventions & important notes
- Authentication: API requests authenticate via `X-API-KEY` header or `api_key` query parameter; environment variable `PI_SERVER_API_KEY` stores the secret.
- Python components: use `requirements.txt` and virtualenvs for isolation.
- Android: use the Gradle wrapper (`gradlew.bat` / `gradlew`) — do not assume system Gradle.
- There is no centralized CI; run component-specific checks locally.

Where to look first
- `AGENTS.md` — repository-wide agent guidance: [AGENTS.md](AGENTS.md)
- Pi server: [pi_server/README.md](pi_server/README.md)
- UI Dashboard: [ui_dashboard/README.md](ui_dashboard/README.md)
- Android: [android_app/README.md](android_app/README.md)

If you want per-component agent files
- I can create `agent-pi-server.md`, `agent-ui-dashboard.md`, or `agent-android.md` with detailed run/test hooks and troubleshooting notes.
