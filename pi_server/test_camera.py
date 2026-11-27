import unittest
from unittest.mock import patch

import camera


class FakeEncoder:
    def __init__(self):
        self.output = None
        self.frame_skip_count = 1


class FakePicamera2:
    def __init__(self):
        self.encoders = []

    def create_video_configuration(self, main, lores):
        return {"main": main, "lores": lores}

    def configure(self, config):
        self.config = config

    def start_encoder(self, encoder, output, name=None):
        encoder.output = output
        encoder.name = name
        self.encoders.append(encoder)

    def start(self):
        pass

    def stop_encoder(self, encoder):
        self.encoders.remove(encoder)


class CameraStreamTests(unittest.TestCase):
    def test_live_frames_continue_during_recording(self):
        with patch.object(camera, "Picamera2", FakePicamera2), \
                patch.object(camera, "H264Encoder", FakeEncoder), \
                patch.object(camera, "JpegEncoder", FakeEncoder), \
                patch.object(camera.time, "sleep"):
            stream = camera.CameraStream()
            frame_generator = stream.frame_generator()
            try:
                stream.start_recording("motion.h264")
                stream._stream_output.outputframe(b"jpeg-frame")

                self.assertEqual(next(frame_generator), b"jpeg-frame")
                self.assertEqual(len(stream.camera.encoders), 2)
                self.assertEqual(stream._recording_encoder.output, "motion.h264")
                self.assertEqual(stream._stream_encoder.name, "lores")
                self.assertEqual(stream._recording_encoder.name, "main")
                self.assertEqual(stream._stream_encoder.frame_skip_count, 2)

                stream.stop_recording()
                self.assertEqual(stream.camera.encoders, [stream._stream_encoder])
            finally:
                frame_generator.close()
                stream.stop_recording()


if __name__ == "__main__":
    unittest.main()
