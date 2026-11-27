import logging
import threading
import time

logger = logging.getLogger(__name__)

try:
    from picamera2 import Picamera2
except ImportError:
    logger.warning("Picamera2 library is unavailable")
    Picamera2 = None

try:
    from picamera2.encoders import H264Encoder, JpegEncoder
except ImportError:
    H264Encoder = None
    JpegEncoder = None

try:
    from picamera2.outputs import Output
except ImportError:
    class Output:
        def __init__(self):
            pass

from config import Config


class _MJPEGStreamOutput(Output):
    def __init__(self):
        super().__init__()
        self._condition = threading.Condition()
        self._frame = None
        self._sequence = 0

    def outputframe(self, frame, keyframe=True, timestamp=None, packet=None, audio=False):
        with self._condition:
            self._frame = bytes(frame)
            self._sequence += 1
            self._condition.notify_all()

    def wait_for_frame(self, previous_sequence, timeout):
        with self._condition:
            if self._sequence == previous_sequence:
                self._condition.wait(timeout)
            if self._sequence == previous_sequence:
                return None, previous_sequence
            return self._frame, self._sequence

    def wake(self):
        with self._condition:
            self._condition.notify_all()


class CameraStream:
    def __init__(self):
        self.camera = None
        self._camera_enabled = True
        self._recording = False
        self._recording_encoder = None
        self._capture_lock = threading.RLock()
        self._stream_output = _MJPEGStreamOutput()
        self._stream_encoder = None
        self._init_camera()

    def _init_camera(self):
        if Picamera2 is None:
            raise RuntimeError("Picamera2 library is required for camera streaming")
        if JpegEncoder is None:
            raise RuntimeError("Picamera2 JPEG encoder support is required for streaming")

        self.camera = Picamera2()
        lores_resolution = (
            Config.CAMERA_RESOLUTION[0] // 2,
            Config.CAMERA_RESOLUTION[1] // 2,
        )
        config = self.camera.create_video_configuration(
            main={"size": Config.CAMERA_RESOLUTION, "format": "YUV420"},
            lores={"size": lores_resolution, "format": "YUV420"},
        )
        self.camera.configure(config)
        self._stream_encoder = JpegEncoder()
        self._stream_encoder.frame_skip_count = 2
        self.camera.start_encoder(
            self._stream_encoder, self._stream_output, name="lores"
        )
        self.camera.start()
        time.sleep(2)

    def is_camera_enabled(self):
        """Check if camera is currently enabled."""
        return self._camera_enabled

    def set_camera_state(self, enabled):
        """Enable or disable camera streaming."""
        self._camera_enabled = enabled
        self._stream_output.wake()

    def start_recording(self, output_path):
        if self.camera is None:
            raise RuntimeError("Camera is not initialized")
        if H264Encoder is None:
            raise RuntimeError("Picamera2 H.264 encoder support is required for recording")

        with self._capture_lock:
            if self._recording:
                raise RuntimeError("A camera recording is already active")
            encoder = H264Encoder()
            self.camera.start_encoder(encoder, str(output_path), name="main")
            self._recording_encoder = encoder
            self._recording = True

    def stop_recording(self):
        with self._capture_lock:
            if not self._recording:
                return
            self.camera.stop_encoder(self._recording_encoder)
            self._recording_encoder = None
            self._recording = False

    def frame_generator(self):
        if self.camera is None:
            self._init_camera()

        sequence = 0
        while self._camera_enabled:
            frame, sequence = self._stream_output.wait_for_frame(sequence, 0.5)
            if frame is not None:
                yield frame
