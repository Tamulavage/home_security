import json
import logging
import math
import os
import threading
import time
from datetime import datetime, timezone

from flask import Flask, Response, abort, jsonify, request

from config import Config
from camera import CameraStream
## TODO : FIx notifications import
#from notifications import NotificationClient
from sensors import SensorReader

app = Flask(__name__)
Config.validate()

sensor_reader = SensorReader()
camera_stream = None
camera_enabled = True
motion_notified = False
lock = threading.Lock()
camera_lock = threading.Lock()
recording_lock = threading.Lock()
recording_operation_lock = threading.Lock()
recording_disabled_until = 0.0
recording_suppressed_motion = False
recording_active = False
DEVICE_STORE_PATH = os.path.join(os.path.dirname(__file__), "devices.json")
logger = logging.getLogger(__name__)


def _load_registered_devices():
    if not os.path.exists(DEVICE_STORE_PATH):
        return []
    with open(DEVICE_STORE_PATH, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass
    return []


def _save_registered_devices(devices):
    with open(DEVICE_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(devices, f, indent=2)


def _require_api_key():
    api_key = request.headers.get("X-API-KEY") or request.args.get("api_key")
    if api_key != Config.API_KEY:
        abort(401, description="Invalid API key")


def authenticated(func):
    def wrapper(*args, **kwargs):
        _require_api_key()
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


def _get_camera_stream():
    global camera_stream
    with camera_lock:
        if camera_stream is None:
            camera_stream = CameraStream()
        return camera_stream


def _start_motion_recording():
    global recording_active
    with recording_operation_lock:
        with recording_lock:
            if (
                recording_active
                or recording_suppressed_motion
                or time.monotonic() < recording_disabled_until
            ):
                return

        Config.RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
        filename = "motion_{}.h264".format(timestamp)

        output_path = Config.RECORDINGS_DIR / filename
        _get_camera_stream().start_recording(output_path)
        with recording_lock:
            recording_active = True
        logger.info("Started motion recording: %s", output_path)


def _stop_motion_recording():
    global recording_active
    with recording_operation_lock:
        with recording_lock:
            if not recording_active:
                return

        _get_camera_stream().stop_recording()
        with recording_lock:
            recording_active = False
        logger.info("Stopped motion recording")


def stream_frames():
    global camera_enabled
    if not camera_enabled:
        abort(503, description="Camera is currently disabled")

    for frame in _get_camera_stream().frame_generator():
        if not camera_enabled:
            break
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


@app.route("/status", methods=["GET"])
@authenticated
def status():
    with recording_lock:
        disabled_remaining = max(
            0.0, recording_disabled_until - time.monotonic()
        )
        paused_until_motion_clears = recording_suppressed_motion
        recording_paused = (
            paused_until_motion_clears or disabled_remaining > 0
        )
        is_recording = recording_active

    return jsonify({
        **sensor_reader.get_status(),
        "camera_enabled": camera_enabled,
        "recording_active": is_recording,
        "recording_in_progress": is_recording,
        "recording_paused": recording_paused,
        "recording_paused_until_motion_clears": paused_until_motion_clears,
        "recording_disabled_remaining_seconds": round(disabled_remaining, 1),
    })


@app.route("/temperature", methods=["GET"])
@authenticated
def temperature():
    return jsonify({
        "temperature_c": sensor_reader.temperature_c,
        "temperature_f": sensor_reader.temperature_f,
        "humidity": sensor_reader.humidity,
    })


@app.route("/motion", methods=["GET"])
@authenticated
def motion():
    with recording_lock:
        paused_until_motion_clears = recording_suppressed_motion
    return jsonify({
        "motion_detected": sensor_reader.motion_detected,
        "motion_last_seen": sensor_reader.last_motion_at,
        "recording_paused_until_motion_clears": paused_until_motion_clears,
    })


@app.route("/video_feed", methods=["GET"])
def video_feed():
    _require_api_key()
    return Response(stream_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/camera/start", methods=["POST"])
@authenticated
def camera_start():
    logger.info("Starting camera")
    global camera_enabled
    camera_enabled = True
    if camera_stream is not None:
        camera_stream.set_camera_state(True)
    return jsonify({"status": "camera_enabled"})


@app.route("/camera/stop", methods=["POST"])
@authenticated
def camera_stop():
    global camera_enabled
    camera_enabled = False
    if camera_stream is not None:
        camera_stream.set_camera_state(False)
    return jsonify({"status": "camera_disabled"})


@app.route("/recording/disable", methods=["POST"])
@authenticated
def recording_disable():
    global recording_disabled_until, recording_suppressed_motion

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        abort(400, description="Expected a JSON payload")

    duration = payload.get("duration_seconds")
    during_current_motion = payload.get("during_current_motion")
    if duration is not None and during_current_motion is not None:
        abort(400, description="Provide duration_seconds or during_current_motion, not both")

    if duration is not None:
        if isinstance(duration, bool):
            abort(400, description="duration_seconds must be a positive number")
        try:
            duration = float(duration)
        except (TypeError, ValueError):
            abort(400, description="duration_seconds must be a positive number")
        if not math.isfinite(duration) or duration <= 0:
            abort(400, description="duration_seconds must be a positive number")

        with recording_lock:
            recording_disabled_until = max(
                recording_disabled_until, time.monotonic() + duration
            )
        _stop_motion_recording()
        return jsonify({
            "trigger_disabled": True,
            "disabled_for_seconds": duration,
        })

    if during_current_motion is not True:
        abort(400, description="Provide duration_seconds or set during_current_motion to true")
    if not sensor_reader.motion_detected:
        abort(409, description="There is no active motion to suppress")

    with recording_lock:
        recording_suppressed_motion = True
    _stop_motion_recording()
    return jsonify({
        "trigger_disabled": True,
        "during_current_motion": True,
    })


@app.route("/register_device", methods=["POST"])
@authenticated
def register_device():
    payload = request.get_json(silent=True)
    if not payload:
        abort(400, description="Expected JSON payload")

    device_id = payload.get("device_id")
    fcm_token = payload.get("fcm_token")
    if not device_id or not fcm_token:
        abort(400, description="device_id and fcm_token are required")

    devices = _load_registered_devices()
    existing = next((d for d in devices if d.get("device_id") == device_id), None)
    if existing:
        existing["fcm_token"] = fcm_token
    else:
        devices.append({"device_id": device_id, "fcm_token": fcm_token})
    _save_registered_devices(devices)
    return jsonify({"registered": True, "device_id": device_id})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


def _motion_monitor():
    global motion_notified
    if not Config.FCM_SERVER_KEY:
        return

    client = NotificationClient()
    while True:
        if sensor_reader.motion_detected:
            with lock:
                if not motion_notified:
                    registered = _load_registered_devices()
                    tokens = [d["fcm_token"] for d in registered if d.get("fcm_token")]
                    if tokens:
                        try:
                            client.send_motion_alert(tokens)
                        except Exception:
                            pass
                    motion_notified = True
        else:
            with lock:
                motion_notified = False
        time.sleep(1)


def _motion_recording_monitor():
    global recording_suppressed_motion
    previous_motion = False
    while True:
        motion_detected = sensor_reader.motion_detected
        should_start_recording = False
        should_stop_recording = False
        with recording_lock:
            if not motion_detected:
                if previous_motion and recording_suppressed_motion:
                    recording_suppressed_motion = False
                    logger.info(
                        "Current-motion recording pause ended because motion cleared"
                    )
                should_stop_recording = True
            elif not previous_motion:
                if (
                    time.monotonic() >= recording_disabled_until
                    and not recording_suppressed_motion
                ):
                    should_start_recording = True

        if should_stop_recording:
            try:
                _stop_motion_recording()
            except Exception:
                logger.exception("Failed to stop motion recording")
        elif should_start_recording:
            try:
                _start_motion_recording()
            except Exception:
                logger.exception("Failed to start motion recording")

        previous_motion = motion_detected
        time.sleep(0.25)


def _set_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = Config.ALLOWED_ORIGINS
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-KEY"
    return response


@app.after_request
def after_request(response):
    return _set_cors_headers(response)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        sensor_reader.start()
        monitor_thread = threading.Thread(target=_motion_monitor, daemon=True)
        monitor_thread.start()
        recording_thread = threading.Thread(
            target=_motion_recording_monitor,
            daemon=True,
            name="motion-recording-monitor",
        )
        recording_thread.start()
        app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, threaded=True)
    finally:
        sensor_reader.stop()
    

if __name__ == "__main__":
    main()
    sensor_reader.stop()
