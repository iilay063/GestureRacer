"""
HSV-based red-laser dot tracker (stretch-goal fallback).

If MediaPipe loses the hand for too long, the main loop asks this module
for a laser position to follow instead. Red wraps the hue circle, so we
mask two ranges and union them.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

import config


@dataclass
class Laser:
    position: Tuple[float, float]  # centroid, normalised 0..1


def detect(frame_bgr: np.ndarray) -> Optional[Laser]:
    import cv2
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)

    mask_lo = cv2.inRange(hsv,
                          np.array(config.LASER_HSV_LOW_1),
                          np.array(config.LASER_HSV_HIGH_1))
    mask_hi = cv2.inRange(hsv,
                          np.array(config.LASER_HSV_LOW_2),
                          np.array(config.LASER_HSV_HIGH_2))
    mask = cv2.bitwise_or(mask_lo, mask_hi)

    moments = cv2.moments(mask)
    if moments["m00"] < config.LASER_MIN_AREA_PX:
        return None

    cx = moments["m10"] / moments["m00"]
    cy = moments["m01"] / moments["m00"]
    h, w = frame_bgr.shape[:2]
    return Laser(position=(cx / w, cy / h))
