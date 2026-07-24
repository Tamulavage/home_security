# Copilot Instructions — Security Repo

Short guidance for AI coding agents working in this repository.

What this repo contains
- `pi_server/` — Flask-based Raspberry Pi server (see pi_server/README.md).
- `ui_dashboard/` — PyQt5 desktop dashboard (see ui_dashboard/README.md).
- `android_app/` — Native Android app; builds with Gradle wrapper (see android_app/README.md).

Primary goals for agents
- Discover where to run and test code: check the component READMEs first.
- Preserve existing documentation; link to it rather than copying.
- Prefer minimal, focused edits; do not change Android Gradle settings unless requested.

Quick run commands
- Pi server (Raspberry Pi / Linux):
  ```bash
  python3 -m venv env
  source env/bin/activate
  pip install -r pi_server/requirements.txt
  python pi_server/app.py
  ```
- UI dashboard (desktop):
  ```bash
  pip install -r ui_dashboard/requirements.txt
  python -m ui_dashboard.main
  ```
- Android (Windows):
  ```powershell
  cd android_app
  .\gradlew.bat assembleDebug
  ```

Conventions & secrets
- `PI_SERVER_API_KEY` environment variable secures API endpoints; requests accept `X-API-KEY` header or `api_key` query param.
- Python components use `requirements.txt`; prefer virtualenvs for isolation.
- Android uses the Gradle wrapper — do not assume system Gradle availability.

Testing & CI
- There is no centralized CI configuration in the repo. Run component-specific checks locally.

Where to look first
- AGENTS guidance: [AGENTS.md](../AGENTS.md)
- Pi server: [pi_server/README.md](../pi_server/README.md)
- UI Dashboard: [ui_dashboard/README.md](../ui_dashboard/README.md)
- Android: [android_app/README.md](../android_app/README.md)

If you need a different format
- I can export these instructions to the repo root or expand per-component agent skill files (e.g., `agent-pi-server.md`).
