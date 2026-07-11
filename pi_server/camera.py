import io
import time

try:
    from picamera2 import Picamera2
except ImportError:
    print("import camera failed")
    Picamera2 = None

from config import Config

class CameraStream:
    def __init__(self):
        self.camera = None
        self._camera_enabled = True
        self._init_camera()

    def _init_camera(self):
        if Picamera2 is None:
            raise RuntimeError("Picamera2 library is required for camera streaming")

        self.camera = Picamera2()
        config = self.camera.create_preview_configuration(
            main={"size": Config.CAMERA_RESOLUTION}
        )
        self.camera.configure(config)
        self.camera.start()
        time.sleep(2)

    def is_camera_enabled(self):
        """Check if camera is currently enabled."""
        return self._camera_enabled

    def set_camera_state(self, enabled):
        """Enable or disable camera streaming."""
        self._camera_enabled = enabled

    def frame_generator(self):
        if self.camera is None:
            self._init_camera()

        stream = io.BytesIO()
        while True:
            if not self._camera_enabled:
                return

            stream.seek(0)
            stream.truncate()
            self.camera.capture_file(stream, format="jpeg")
            stream.seek(0)
            frame = stream.read()
            yield frame
