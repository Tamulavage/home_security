import json
import requests

from config import Config

FCM_URL = "https://fcm.googleapis.com/fcm/send"

class NotificationClient:
    def __init__(self):
        if not Config.FCM_SERVER_KEY:
            raise ValueError("FCM_SERVER_KEY is not configured")
        self.server_key = Config.FCM_SERVER_KEY

    def send_motion_alert(self, fcm_tokens, title="Motion detected", body="Movement was detected by your Raspberry Pi security system."):
        headers = {
            "Authorization": f"key={self.server_key}",
            "Content-Type": "application/json",
        }
        data = {
            "registration_ids": fcm_tokens,
            "notification": {
                "title": title,
                "body": body,
                "sound": "default",
            },
            "data": {
                "event": "motion_detected",
                "timestamp": int(time.time()),
            },
        }
        response = requests.post(FCM_URL, headers=headers, data=json.dumps(data), timeout=10)
        response.raise_for_status()
        return response.json()
