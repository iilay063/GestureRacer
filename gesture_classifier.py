"""
Classify a Hand into one of a small vocabulary of gestures.

Rule-based, not learned. Each rule asks which fingers are extended
relative to their PIP joint. Robust to scale and good enough for five
well-separated gestures.

Vocabulary (per CLAUDE.md):
    OPEN_PALM   -> STOP
    FIST        -> forward
    THUMBS_UP   -> spin 360 degrees
    PEACE       -> reverse
    POINT       -> follow the fingertip
"""

from enum import Enum
from typing import List, Tuple

import config
from hand_tracker import Hand


class Gesture(Enum):
    UNKNOWN = "unknown"
    OPEN_PALM = "open_palm"
    FIST = "fist"
    THUMBS_UP = "thumbs_up"
    PEACE = "peace"
    POINT = "point"


def _hand_height(landmarks: List[Tuple[float, float]]) -> float:
    ys = [y for _, y in landmarks]
    return max(ys) - min(ys)


def _finger_extended(landmarks: List[Tuple[float, float]],
                     tip_idx: int,
                     pip_idx: int,
                     hand_h: float) -> bool:
    # Image Y grows downwards, so "tip above pip" means tip_y < pip_y.
    margin = config.FINGER_EXTENDED_MARGIN * max(hand_h, 1e-6)
    return landmarks[pip_idx][1] - landmarks[tip_idx][1] > margin


def _thumb_extended(landmarks: List[Tuple[float, float]]) -> bool:
    # The thumb bends sideways, so compare X coordinates instead of Y.
    # The wrist tells us which side of the hand the thumb is on, which
    # mirrors for left vs right hands.
    tip_x = landmarks[4][0]
    ip_x = landmarks[2][0]
    wrist_x = landmarks[0][0]
    if ip_x > wrist_x:
        return tip_x > ip_x  # right hand seen palm-out
    return tip_x < ip_x      # left hand mirror


def classify(hand: Hand) -> Gesture:
    lm = hand.landmarks
    hand_h = _hand_height(lm)

    extended = {
        "thumb":  _thumb_extended(lm),
        "index":  _finger_extended(lm, 8, 6, hand_h),
        "middle": _finger_extended(lm, 12, 10, hand_h),
        "ring":   _finger_extended(lm, 16, 14, hand_h),
        "pinky":  _finger_extended(lm, 20, 18, hand_h),
    }

    fingers_up = sum(1 for v in extended.values() if v)

    if fingers_up == 5:
        return Gesture.OPEN_PALM
    if fingers_up == 0:
        return Gesture.FIST
    if extended["thumb"] and not any(extended[f]
                                     for f in ("index", "middle", "ring", "pinky")):
        return Gesture.THUMBS_UP
    if (extended["index"] and extended["middle"]
            and not extended["ring"] and not extended["pinky"]):
        return Gesture.PEACE
    if (extended["index"] and not extended["middle"]
            and not extended["ring"] and not extended["pinky"]):
        return Gesture.POINT
    return Gesture.UNKNOWN
