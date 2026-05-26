"""
GestureRacer entry point.

Pipeline:
    frame -> hand_tracker -> gesture
    mic   -> voice_listener -> command
    arbiter -> robot_controller

Voice commands latch for config.VOICE_LATCH_SEC. During the latch
window the spoken command drives the robot and gestures are ignored.
After the window expires, gestures take over again if a hand is visible.
Stops on extended absence of any signal, or on any unhandled exception.
"""

import argparse
import faulthandler
import time

# Dump a Python traceback to stderr on segfault instead of dying silently.
faulthandler.enable()

import config
from camera import Camera
from gesture_classifier import Gesture, classify
from hand_tracker import HandTracker
from robot_controller import RobotController


def main() -> None:
    parser = argparse.ArgumentParser(description="Hand- and voice-controlled JetRacer.")
    parser.add_argument("--no-motors", action="store_true",
                        help="Run vision/voice pipeline only; do not drive motors.")
    parser.add_argument("--no-voice", action="store_true",
                        help="Disable the voice channel (gesture only).")
    parser.add_argument("--debug", action="store_true",
                        help="Show OpenCV debug window and print voice match confidences.")
    args = parser.parse_args()

    camera = Camera()
    tracker = HandTracker()
    robot = RobotController(use_motors=not args.no_motors)

    # Voice is optional - if model/mic isn't available we degrade to
    # gesture-only rather than refusing to start.
    voice = None
    if not args.no_voice:
        try:
            from voice_listener import VoiceListener
            voice = VoiceListener(verbose=args.debug)
            voice.start()
            print("[voice] listening")
        except Exception as exc:
            print(f"[voice] disabled: {exc!r}")
            voice = None

    last_any_seen = time.time()
    last_frame_time = time.time()
    # Tracks which voice command was last acted upon, so we only log
    # mode transitions instead of every frame.
    last_acted_voice_time = 0.0

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

            # Voice latch: a recent voice command takes priority over
            # whatever the camera sees, so a steady hand pose doesn't
            # immediately override the spoken command.
            voice_cmd, voice_cmd_time = (None, 0.0)
            if voice is not None:
                voice_cmd, voice_cmd_time = voice.latest()
            voice_active = (voice_cmd is not None
                            and (now - voice_cmd_time) < config.VOICE_LATCH_SEC)

            hand = tracker.detect(frame)
            gesture = Gesture.UNKNOWN

            if voice_active:
                last_any_seen = now
                robot.execute_voice(voice_cmd)
                if voice_cmd_time != last_acted_voice_time:
                    print(f"[voice] -> {voice_cmd!r}")
                    last_acted_voice_time = voice_cmd_time
            elif hand is not None:
                last_any_seen = now
                gesture = classify(hand)
                # POINT mode follows the fingertip directly (landmark 8);
                # every other gesture follows the palm centre.
                target = hand.landmarks[8] if gesture == Gesture.POINT else hand.center
                robot.execute(gesture, target, hand.size)

            # Highest-priority safety rule: no detection for too long => stop.
            if now - last_any_seen >= config.SAFETY_STOP_SEC:
                robot.stop()

            if config.PRINT_DIAGNOSTICS:
                mode = "voice" if voice_active else "gesture"
                print(f"[loop] fps={fps:5.1f}  mode={mode:7s}"
                      f"  gesture={gesture.value}"
                      f"  hand={'yes' if hand else 'no '}")

            if overlay is not None:
                overlay.draw(frame, hand=hand, gesture=gesture, fps=fps)

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
        if voice is not None:
            voice.stop()
        if overlay is not None:
            overlay.close()


if __name__ == "__main__":
    main()
