import time
import threading
import adafruit_dht
import RPi.GPIO as GPIO
    
import board
from config import Config

# TODO: change D5 to pull from config 
dht_device = adafruit_dht.DHT11(board.D5, use_pulseio=False)


class SensorReader:
    def __init__(self):
        self.temperature_c = None
        self.temperature_f = None
        self.humidity = None
        self.motion_detected = False
        self.last_motion_at = None
        self._stop = threading.Event()
        self._dht_thread = None
        self._motion_thread = None

        if GPIO:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(Config.PIR_PIN, GPIO.IN)

    def read_dht(self):
        if not dht_device:
            return None, None, None
        
        print("dht read")
        try:
            temperature = dht_device.temperature
            humidity = dht_device.humidity
            if humidity is not None and temperature is not None:
                self.temperature_c = round(temperature, 1)
                self.temperature_f = round((temperature* (9 / 5) + 32),2)
                self.humidity = round(humidity, 1)
            time.sleep(600)
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            print(error.args[0])
        except Exception as error:
            dht_device.exit()
            raise error


        return self.temperature_c, self.humidity, self.temperature_f

    def _poll_dht(self):
        while not self._stop.is_set():
            self.read_dht()
            if self._stop.wait(Config.SENSOR_READ_INTERVAL_SECONDS):
                break

    def _poll_motion(self):
        if not GPIO:
            return

        while not self._stop.is_set():
            state = GPIO.input(Config.PIR_PIN)
            if state == GPIO.HIGH:
                self.motion_detected = True
                self.last_motion_at = time.time()
                print("Active Motion")
            else:
                if self.last_motion_at and (time.time() - self.last_motion_at) > Config.MOTION_RESET_SECONDS:
                    self.motion_detected = False
                    
                    print("No Motion")
            time.sleep(10)

    def start(self):
        if self._dht_thread and self._dht_thread.is_alive():
            return

        self._stop.clear()
        self._dht_thread = threading.Thread(target=self._poll_dht, daemon=True, name="dht-poller")
        self._dht_thread.start()

        self._motion_thread = threading.Thread(target=self._poll_motion, daemon=True, name="motion-poller")
        self._motion_thread.start()

    def stop(self):
        self._stop.set()
        for thread in (self._dht_thread, self._motion_thread):
            if thread and thread.is_alive():
                thread.join(timeout=2)

        if dht_device:
            dht_device.exit()
        if GPIO:
            GPIO.cleanup()
        print("sensors exited")

    def get_status(self):
        return {
            "temperature_c": self.temperature_c,
            "temperature_f": self.temperature_f,
            "humidity": self.humidity,
            "motion_detected": self.motion_detected,
            "motion_last_seen": self.last_motion_at,
        }
