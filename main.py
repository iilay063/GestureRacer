"""
GestureRacer entry point.

Pipeline:
    frame -> hand_tracker -> gesture -> robot_controller
Falls back to laser tracking if the hand is lost for too long. Stops on
extended absence of any signal, or on any unhandled exception.
"""

import argparse
import faulthandler
import time

# Dump a Python traceback to stderr on segfault instead of dying silently.
faulthandler.enable()

import config
import laser_tracker
from camera import Camera
from gesture_classifier import Gesture, classify
from hand_tracker import HandTracker
from robot_controller import RobotController


def main() -> None:
    parser = argparse.ArgumentParser(description="Hand-tracking JetRacer.")
    parser.add_argument("--no-motors", action="store_true",
                        help="Run vision pipeline only; do not drive motors.")
    parser.add_argument("--debug", action="store_true",
                        help="Show OpenCV debug window with overlays.")
    args = parser.parse_args()

    camera = Camera()
    tracker = HandTracker()
    robot = RobotController(use_motors=not args.no_motors)

    last_hand_seen = time.time()
    last_any_seen = time.time()
    last_frame_time = time.time()

    overlay = None
    if args.debug or config.SHOW_DEBUG_WINDOW:
        from utils.visualization import DebugOverlay
        overlay = DebugOverlay()

    try:
        while True:
            frame = camera.read()
            if frame is None:
                time.sleep(0.01)
                continue

            now = time.time()
            fps = 1.0 / max(now - last_frame_time, 1e-6)
            last_frame_time = now

            hand = tracker.detect(frame)
            gesture = Gesture.UNKNOWN
            laser = None

            if hand is not None:
                last_hand_seen = now
                last_any_seen = now
                gesture = classify(hand)
                # POINT mode follows the fingertip directly (landmark 8);
                # every other gesture follows the palm centre.
                target = hand.landmarks[8] if gesture == Gesture.POINT else hand.center
                robot.execute(gesture, target, hand.size)
            else:
                hand_lost_for = now - last_hand_seen
                if hand_lost_for >= config.HAND_LOST_LASER_SWITCH_SEC:
                    laser = laser_tracker.detect(frame)
                    if laser is not None:
                        last_any_seen = now
                        robot.steer_toward(laser.position,
                                           throttle=config.FORWARD_THROTTLE)

            # Highest-priority safety rule: no detection for too long => stop.
            if now - last_any_seen >= config.SAFETY_STOP_SEC:
                robot.stop()

            if config.PRINT_DIAGNOSTICS:
                print(f"[loop] fps={fps:5.1f}  gesture={gesture.value}"
                      f"  hand={'yes' if hand else 'no'}"
                      f"  laser={'yes' if laser else 'no'}")

            if overlay is not None:
                overlay.draw(frame, hand=hand, gesture=gesture,
                             laser=laser, fps=fps)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as exc:
        # Safety: any unhandled exception must not leave the motors running.
        print(f"[fatal] {exc!r}")
        raise
    finally:
        robot.stop()
        tracker.close()
        camera.release()
        if overlay is not None:
            overlay.close()


if __name__ == "__main__":
    main()
