# GestureRacer

Hand-gesture-controlled robot car. Final project for **Software Development for Human & Robot Humanoid Interaction** (HIT, Computer Science).

The robot uses its onboard camera to find the user's hand, steers toward it, and reacts to a small vocabulary of gestures as movement commands.

## Hardware

- NVIDIA Jetson Nano (128-core Maxwell GPU)
- Waveshare JetRacer Pro AI Kit (Ackermann steering: front servo, rear drive)
- Raspberry Pi Camera v2 over CSI

## How it works

```
frame -> hand_tracker -> gesture_classifier -> robot_controller
```

The main loop runs synchronously at camera FPS. If MediaPipe loses the hand for 2 s the robot falls back to an HSV red-laser tracker. If nothing is detected for 3 s the safety stop cuts the motors.

## Gesture vocabulary

| Gesture           | Command                              |
|-------------------|--------------------------------------|
| Open palm         | Stop                                 |
| Closed fist       | Drive forward (still steers to hand) |
| Thumbs up         | Spin in place                        |
| Peace sign        | Reverse                              |
| Index finger only | Follow the fingertip                 |
| (no clear gesture)| Follow hand, throttle scales with distance |

## Setup

The Jetson should already have OpenCV, `jetracer` and `jetcam` from the JetRacer SD image. Install MediaPipe separately:

```bash
pip3 install mediapipe opencv-python
```

## Run

```bash
# Safe to run on a desk - vision pipeline only, motors disabled.
python3 main.py --no-motors --debug

# Full system. Test on an open floor.
python3 main.py

# Camera smoke test.
python3 camera.py
```

All tunable values live in `config.py`. Calibrate there first, not in code.

## Project layout

| File | Role |
|------|------|
| `main.py` | Entry point and main loop |
| `config.py` | All thresholds, gains and timeouts |
| `camera.py` | CSI camera wrapper via jetcam |
| `hand_tracker.py` | MediaPipe Hands - returns 21 landmarks |
| `gesture_classifier.py` | Rule-based landmarks -> gesture |
| `laser_tracker.py` | HSV red-dot fallback |
| `robot_controller.py` | jetracer wrapper - gesture -> motors |
| `utils/visualization.py` | Optional OpenCV debug overlay |

## Safety

- Throttle is hard-capped at `MAX_THROTTLE = 0.3` during development.
- The main loop's `finally` block always calls `robot.stop()`.
- Safety stop kicks in after 3 s of no detection of any kind.
- Default to `--no-motors` until each new feature is hardware-tested.
- Always test on the floor. Never on a table.

## Course-topic mapping

| Component | Course topic |
|-----------|--------------|
| `camera.py` + OpenCV frame handling | Embedded computer vision |
| `hand_tracker.py` (MediaPipe on GPU) | Embedded deep learning |
| `gesture_classifier.py` | Gesture recognition |
| `robot_controller.steer_toward` (image position as feedback signal) | Closed-loop control |
| `robot_controller.py` (servo + motor coordination) | Mechatronics basics |

## Status

See `TODO.md` for open questions and tunables that still need on-hardware calibration.
# GestureRacer
