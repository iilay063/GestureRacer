"""
Central configuration for the GestureRacer project.

All tunable values live here so the rest of the code is free of magic
numbers. Adjust thresholds, control gains and detection parameters here
when calibrating on real hardware.
"""

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
# 224x224 keeps MediaPipe fast on the Nano's Maxwell GPU. Raise if
# classification accuracy suffers at the cost of FPS.
CAMERA_WIDTH = 224
CAMERA_HEIGHT = 224
CAMERA_FPS = 30

# ---------------------------------------------------------------------------
# Hand tracker (MediaPipe Hands)
# ---------------------------------------------------------------------------
# Single hand is enough for this project and roughly halves inference time.
HAND_MAX_HANDS = 1
HAND_DETECTION_CONFIDENCE = 0.6
HAND_TRACKING_CONFIDENCE = 0.5

# ---------------------------------------------------------------------------
# Gesture classifier
# ---------------------------------------------------------------------------
# A finger counts as "extended" when its tip clears its PIP joint by at
# least this fraction of the hand's bounding-box height. Scale-invariant
# so it works the same whether the hand is near or far from the camera.
FINGER_EXTENDED_MARGIN = 0.02

# ---------------------------------------------------------------------------
# Robot control
# ---------------------------------------------------------------------------
# Safety cap during development. Do not raise without supervision.
MAX_THROTTLE = 0.3

# Throttle for the closed-fist "forward" gesture.
FORWARD_THROTTLE = 0.2

# Throttle for the peace-sign "reverse" gesture. Negative = reverse.
REVERSE_THROTTLE = -0.15

# Throttle while spinning in place for the thumbs-up gesture.
SPIN_THROTTLE = 0.15

# Spin direction: +1 = clockwise (steer right), -1 = counter-clockwise.
# Up for review with the lecturer; flipped here means flipped everywhere.
SPIN_DIRECTION = 1

# Steering gain for the closed-loop "follow the hand" controller.
# Higher = sharper turns for the same horizontal hand offset.
STEERING_GAIN = 1.5

# Hand bounding-box width thresholds (fraction of frame width) used to
# scale forward throttle: hand close => stop, hand far => full forward.
HAND_SIZE_STOP = 0.5
HAND_SIZE_FAR = 0.15

# ---------------------------------------------------------------------------
# Laser fallback
# ---------------------------------------------------------------------------
# Red wraps the hue circle, so we mask two ranges and union them.
LASER_HSV_LOW_1 = (0, 120, 200)
LASER_HSV_HIGH_1 = (10, 255, 255)
LASER_HSV_LOW_2 = (170, 120, 200)
LASER_HSV_HIGH_2 = (180, 255, 255)
LASER_MIN_AREA_PX = 5  # the dot is tiny; keep this low

# Switch to laser tracking after this many seconds without a hand.
HAND_LOST_LASER_SWITCH_SEC = 2.0

# ---------------------------------------------------------------------------
# Safety stop
# ---------------------------------------------------------------------------
# Cut motors after this long with no detection of any kind.
SAFETY_STOP_SEC = 3.0

# ---------------------------------------------------------------------------
# Debug
# ---------------------------------------------------------------------------
PRINT_DIAGNOSTICS = True
SHOW_DEBUG_WINDOW = False  # requires a display attached to the Jetson
