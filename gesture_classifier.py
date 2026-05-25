"""
Classify a Hand into one of a small vocabulary of gestures.

Rule-based, not learned. Each rule asks which fingers are "extended"
based on whether the MCP->PIP and PIP->tip segments are roughly
collinear. This is rotation-invariant, so the hand can be held at
any angle relative to the camera and the classifier still works.

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


def _finger_extended(landmarks: List[Tuple[float, float]],
                     mcp_idx: int,
                     pip_idx: int,
                     tip_idx: int) -> bool:
    # Treat the finger as two segments meeting at the PIP joint. When the
    # finger is straight they point in nearly the same direction (cosine
    # close to +1). When curled, the tip segment swings around (cosine
    # drops or even goes negative).
    v1x = landmarks[pip_idx][0] - landmarks[mcp_idx][0]
    v1y = landmarks[pip_idx][1] - landmarks[mcp_idx][1]
    v2x = landmarks[tip_idx][0] - landmarks[pip_idx][0]
    v2y = landmarks[tip_idx][1] - landmarks[pip_idx][1]

    mag = ((v1x * v1x + v1y * v1y) ** 0.5) * ((v2x * v2x + v2y * v2y) ** 0.5)
    if mag < 1e-9:
        return False
    cos_angle = (v1x * v2x + v1y * v2y) / mag
    return cos_angle > config.FINGER_STRAIGHTNESS_COS_MIN


def classify(hand: Hand) -> Gesture:
    lm = hand.landmarks

    extended = {
        "thumb":  _finger_extended(lm, 2, 3, 4),
        "index":  _finger_extended(lm, 5, 6, 8),
        "middle": _finger_extended(lm, 9, 10, 12),
        "ring":   _finger_extended(lm, 13, 14, 16),
        "pinky":  _finger_extended(lm, 17, 18, 20),
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
