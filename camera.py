"""
CSI camera wrapper.

Uses jetcam's CSICamera, which talks to the Pi Camera through GStreamer.
cv2.VideoCapture(0) is unreliable on the Jetson Nano - this is the
supported path.
"""

from typing import Optional

import numpy as np

import config


class Camera:
    def __init__(self,
                 width: int = config.CAMERA_WIDTH,
                 height: int = config.CAMERA_HEIGHT,
                 fps: int = config.CAMERA_FPS):
        # Lazy import so the module is still importable on a dev laptop
        # that doesn't have jetcam installed.
        from jetcam.csi_camera import CSICamera
        self._camera = CSICamera(width=width, height=height, capture_fps=fps)
        # Starts jetcam's background grab thread.
        self._camera.running = True

    def read(self) -> Optional[np.ndarray]:
        """Most recent BGR frame, or None if not available yet."""
        return self._camera.value

    def release(self) -> None:
        self._camera.running = False


if __name__ == "__main__":
    # Smoke-test: confirm a frame can be grabbed.
    import time
    cam = Camera()
    print("Warming up camera...")
    time.sleep(1.0)
    frame = cam.read()
    if frame is None:
        print("No frame received.")
    else:
        print(f"Got frame: shape={frame.shape}, dtype={frame.dtype}")
    cam.release()
