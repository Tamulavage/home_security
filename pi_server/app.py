import json
import os
import threading
import time

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
DEVICE_STORE_PATH = os.path.join(os.path.dirname(__file__), "devices.json")


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


def stream_frames():
    global camera_stream, camera_enabled
    if not camera_enabled:
        abort(503, description="Camera is currently disabled")
    
    if camera_stream is None:
        camera_stream = CameraStream()

    for frame in camera_stream.frame_generator():
        if not camera_enabled:
            break
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


@app.route("/status", methods=["GET"])
@authenticated
def status():
    return jsonify({**sensor_reader.get_status(), "camera_enabled": camera_enabled})


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
    return jsonify({
        "motion_detected": sensor_reader.motion_detected,
        "motion_last_seen": sensor_reader.last_motion_at,
    })


@app.route("/video_feed", methods=["GET"])
def video_feed():
    _require_api_key()
    return Response(stream_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/camera/start", methods=["POST"])
@authenticated
def camera_start():
    print("camera starting")
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


def _set_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = Config.ALLOWED_ORIGINS
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-KEY"
    return response


@app.after_request
def after_request(response):
    return _set_cors_headers(response)


def main():
    try:
        sensor_reader.start()
        monitor_thread = threading.Thread(target=_motion_monitor, daemon=True)
        monitor_thread.start()
        app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, threaded=True)
    finally:
        sensor_reader.stop()
    

if __name__ == "__main__":
    main()
    sensor_reader.stop()
