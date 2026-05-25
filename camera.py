"""
CSI camera wrapper.

Uses an explicit GStreamer pipeline through cv2.VideoCapture. The
pipeline pulls NV12 frames from nvarguscamerasrc, downscales/converts
to BGR on the GPU (nvvidconv), then hands off via appsink.

Why not jetcam: jetcam's CSICamera uses an EGL transform stage and a
background grab thread. On Jetson Nano this races with MediaPipe's GPU
context and segfaults inside libArgus mid-inference. The appsink
pipeline is synchronous and EGL-free, which removes that contention.
"""

from typing import Optional

import cv2
import numpy as np

import config


def _gst_pipeline(width: int, height: int, fps: int) -> str:
    # Capture at a native sensor mode (1280x720@30) then downscale on
    # the GPU to the target size. nvvidconv is much cheaper than doing
    # the resize on the CPU.
    return (
        "nvarguscamerasrc sensor-id=0 ! "
        f"video/x-raw(memory:NVMM), width=1280, height=720, "
        f"format=NV12, framerate={fps}/1 ! "
        "nvvidconv flip-method=0 ! "
        f"video/x-raw, width={width}, height={height}, format=BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=BGR ! "
        "appsink drop=true max-buffers=1 sync=false"
    )


class Camera:
    def __init__(self,
                 width: int = config.CAMERA_WIDTH,
                 height: int = config.CAMERA_HEIGHT,
                 fps: int = config.CAMERA_FPS):
        pipeline = _gst_pipeline(width, height, fps)
        self._cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        if not self._cap.isOpened():
            raise RuntimeError(
                "Could not open CSI camera via GStreamer pipeline. "
                "Try: sudo systemctl restart nvargus-daemon"
            )

    def read(self) -> Optional[np.ndarray]:
        """Most recent BGR frame, or None if the read failed."""
        ok, frame = self._cap.read()
        return frame if ok else None

    def release(self) -> None:
        self._cap.release()


if __name__ == "__main__":
    # Smoke-test: confirm a frame can be grabbed.
    cam = Camera()
    print("Warming up camera...")
    frame = cam.read()
    if frame is None:
        print("No frame received.")
    else:
        print(f"Got frame: shape={frame.shape}, dtype={frame.dtype}")
    cam.release()
