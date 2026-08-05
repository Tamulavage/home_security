# AGENTS — Repository Guidance for AI Coding Agents

Purpose
- Give AI agents the minimal facts needed to be productive in this repo.

Quick Commands
- Android (use Gradle wrapper in `android_app`):
  - Windows (from repo root): `cd android_app && .\gradlew.bat assembleDebug`
  - Recommended: open `android_app` in Android Studio for run/debug.
- Pi server (Raspberry Pi):
  - Create & activate venv, then install deps: `python3 -m venv env && source env/bin/activate && python3 -m pip install -r pi_server/requirements.txt`
  - Run: `python3 pi_server/app.py`
- UI Dashboard (desktop):
  - Install deps: `pip install -r ui_dashboard/requirements.txt`
  - Run: `python -m ui_dashboard.main`

Key Files & Components
- `pi_server/app.py` — Flask entrypoint and API endpoints. See [pi_server/README.md](pi_server/README.md).
- `pi_server/config.py` — environment-driven configuration and API key usage.
- `ui_dashboard/main.py` and `ui_dashboard/api_client.py` — desktop app entry and REST client. See [ui_dashboard/README.md](ui_dashboard/README.md).
- `android_app/` — Android app; uses `X-API-KEY` for auth. See [android_app/README.md](android_app/README.md).

Conventions & Important Notes
- Authentication: API requests authenticate via `X-API-KEY` header or `api_key` query parameter; environment variable `PI_SERVER_API_KEY` holds the secret for the server.
- Python projects: use `requirements.txt` for deps. Prefer virtual environments.
- Android: use the Gradle wrapper (`gradlew.bat` / `gradlew`) — do not rely on system Gradle.
- Tests: there are no centralized test runners; run component-specific checks manually (e.g., Android unit/instrumentation tests via Gradle, Python scripts with pytest if added).

Where to look first
- Android overview: [android_app/README.md](android_app/README.md)
- Pi server: [pi_server/README.md](pi_server/README.md)
- UI Dashboard: [ui_dashboard/README.md](ui_dashboard/README.md)

If you want more automation
- I can add a `.github/copilot-instructions.md` or expand this file with task-specific agent skills (e.g., `agent-pi-server.md`) — tell me which area to focus on.
