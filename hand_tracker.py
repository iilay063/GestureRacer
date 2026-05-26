"""
MediaPipe hand detection.

Wraps mp.solutions.hands and returns a single hand's landmarks plus
derived fields (centre, bounding-box width) the rest of the system needs.
Width is used instead of area because it is less affected by finger
curl, which makes it a better proxy for "how close is the hand".
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

import config


@dataclass
class Hand:
    landmarks: List[Tuple[float, float]]  # 21 (x, y) pairs, normalised 0..1
    center: Tuple[float, float]           # palm centre, normalised 0..1
    size: float                           # bounding-box width, normalised


class HandTracker:
    def __init__(self):
        # Lazy + explicit submodule import: dev laptops without
        # mediapipe can still import other modules for unit-testing,
        # and `import mediapipe as mp` does not reliably populate
        # mp.solutions on newer wheels (Python 3.12+).
        from mediapipe.solutions import hands as mp_hands
        self._hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=config.HAND_MAX_HANDS,
            min_detection_confidence=config.HAND_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.HAND_TRACKING_CONFIDENCE,
        )

    def detect(self, frame_bgr: np.ndarray) -> Optional[Hand]:
        # MediaPipe expects RGB.
        import cv2
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self._hands.process(rgb)
        if not results.multi_hand_landmarks:
            return None

        lm = results.multi_hand_landmarks[0].landmark
        points = [(p.x, p.y) for p in lm]

        xs = [x for x, _ in points]
        ys = [y for _, y in points]
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        center = ((x_min + x_max) / 2.0, (y_min + y_max) / 2.0)
        size = x_max - x_min
        return Hand(landmarks=points, center=center, size=size)

    def close(self) -> None:
        self._hands.close()
