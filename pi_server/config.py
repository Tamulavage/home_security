import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    # TODO Move to security file
    FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    API_KEY = os.getenv("PI_SERVER_API_KEY", "changeme")
    DHT_PIN = int(os.getenv("DHT_PIN", "5")) 
    PIR_PIN = int(os.getenv("PIR_PIN", "17"))
    FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY", "")
    CAMERA_RESOLUTION = (640, 480)
    CAMERA_FPS = int(os.getenv("CAMERA_FPS", "24"))
    SENSOR_READ_INTERVAL_SECONDS = float(os.getenv("SENSOR_READ_INTERVAL_SECONDS", "5"))
    MOTION_RESET_SECONDS = float(os.getenv("MOTION_RESET_SECONDS", "10"))
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*")

    @classmethod
    def validate(cls):
        if cls.API_KEY == "changeme":
            raise ValueError("Set PI_SERVER_API_KEY environment variable to a strong secret.")


def get_config():
    return Config
