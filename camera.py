"""
Camera wrapper with auto-fallback.

On the Jetson Nano, prefers the CSI camera via an explicit GStreamer
pipeline (nvarguscamerasrc -> nvvidconv -> appsink). On a laptop or
any non-Jetson machine, falls back to the default USB/built-in webcam
through cv2.VideoCapture(0). Same API either way, so main.py doesn't
care which backend is in use.

Why not jetcam on the Jetson: jetcam's CSICamera uses an EGL transform
stage and a background grab thread. That setup races with MediaPipe's
GPU context and segfaults inside libArgus mid-inference. The appsink
pipeline is synchronous and EGL-free, which removes that contention.
"""

import os
from typing import Optional

import cv2
import numpy as np

import config


def _is_jetson() -> bool:
    # /etc/nv_tegra_release exists only on Jetson devices.
    return os.path.exists("/etc/nv_tegra_release")


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
        # On Jetson, try the CSI pipeline first. Skip it entirely on
        # other machines so we don't print scary "no element
        # nvarguscamerasrc" warnings on a laptop.
        if _is_jetson():
            pipeline = _gst_pipeline(width, height, fps)
            cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            if cap.isOpened():
                self._cap = cap
                self.backend = "CSI"
                print("[camera] using Jetson CSI camera")
                return
            cap.release()
            print("[camera] CSI not available, falling back to USB")

        # USB / laptop webcam path. Webcams often ignore the requested
        # size and pick a native mode instead - MediaPipe handles any
        # size, so we don't enforce it.
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, fps)
            self._cap = cap
            self.backend = "USB"
            print("[camera] using USB / built-in webcam")
            return

        raise RuntimeError(
            "No camera available (tried CSI and USB). On Jetson try "
            "`sudo systemctl restart nvargus-daemon`; on a laptop check "
            "that the webcam isn't held by another app."
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
    print(f"Backend: {cam.backend}")
    frame = cam.read()
    if frame is None:
        print("No frame received.")
    else:
        print(f"Got frame: shape={frame.shape}, dtype={frame.dtype}")
    cam.release()
