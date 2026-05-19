# Open Questions

Track these until answered (per CLAUDE.md).

## From CLAUDE.md

- [ ] Has the CSI camera been verified working on this specific Jetson?
- [ ] Is the `jetracer` library already installed and tested?
- [ ] What's the target demo environment - hallway, lab floor, classroom?
- [ ] Required FPS for smooth tracking? (15? 30?)
- [ ] Are there specific gestures the lecturer wants to see, or is the vocabulary up to the student?
- [ ] Is the OLED display feature in scope, or stretch goal only?

## Tunables needing on-hardware calibration

- [ ] `STEERING_GAIN` - tune so steering is responsive but not twitchy.
- [ ] `HAND_SIZE_STOP` / `HAND_SIZE_FAR` - depend on camera FOV and typical user distance.
- [ ] `SPIN_DIRECTION` and `SPIN_THROTTLE` - which way should "thumbs up" rotate, and how fast?
- [ ] `REVERSE_THROTTLE` - is the chosen reverse speed safe in the demo space?
- [ ] `LASER_HSV_*` - red dot brightness depends on ambient lighting; tune under demo lights.
- [ ] `FINGER_EXTENDED_MARGIN` - if gesture classification feels jittery, raise this.

## Decisions deferred

- [ ] Should `FIST` (forward) still steer toward the hand, or drive straight? Currently steers.
- [ ] In POINT mode, should forward throttle still scale with hand size? Currently yes.
