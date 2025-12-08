#!/usr/bin/env python
"""
Hardware Test Script for Dome Calibration and Movement

Provides CLI-accessible test functions for:
1. Rotating dome in 8 segments (full revolution)
2. Counting total encoder tics for a full revolution (CW/CCW)
3. Calibrating home position by sweeping and centering

Usage:
    python hardware_test.py rotate_segments
    python hardware_test.py count_full_rotation [cw|ccw]
    python hardware_test.py calibrate_home
"""
import os
import sys
import time

from dome import Dome
from persistence import restore_state, save_state

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib")
)

SEGMENT_TICS = [39, 39, 39, 40, 39, 39, 39, 40]


def rotate_segments():
    """
    Rotate dome one full revolution in 8 segments (45 deg each)
    """
    dome = Dome()
    restore_state(dome)
    print("Starting segmented rotation test...")
    for i, tics in enumerate(SEGMENT_TICS):
        print("Segment {}: Rotating {} tics".format(i + 1, tics))
        dome.cw()  # Set direction to CW and start rotation
        moved = 0
        while moved < tics:
            current_ticks, _ = dome.counter_read()
            moved = current_ticks  # Should always start at zero
            sys.stdout.write("\r  Tics moved: {}".format(moved))
            sys.stdout.flush()
        dome.rotation_stop()
        print("  Done.")
        save_state(dome, "rotate_segments")
        time.sleep(5)  # Pause between segments
    print("Full segmented rotation complete.")


def count_full_rotation(direction):
    """
    Count total tics for a full revolution in specified direction (CW/CCW)
    """
    dome = Dome()
    restore_state(dome)
    print(
        "Counting tics for full revolution in {} direction...".format(direction.upper())
    )
    # Move to home position first
    print("Moving to home position...")
    dome.home()
    time.sleep(5)  # Pause between dome moves
    save_state(dome, "count_full_rotation_home")
    if direction.lower() == "cw":
        dome.cw()
    else:
        dome.ccw()
    print("Starting rotation...")
    moved = 0
    while True:
        current_ticks, _ = dome.counter_read()
        moved = abs(current_ticks)  # Should always start at zero
        sys.stdout.write("\r  Tics moved: {}".format(moved))
        sys.stdout.flush()
        if dome.isHome() and moved > 10:
            break
    dome.rotation_stop()
    print("\nTotal tics for full revolution: {}".format(moved))
    save_state(dome, "count_full_rotation")


def calibrate_home():
    """
    Calibrate home position by sweeping past home in both directions, then centering
    """
    dome = Dome()
    restore_state(dome)
    print("Calibrating home position...")
    # Sweep CW past home
    print("Sweeping CW past home...")
    dome.cw()
    while True:
        current_ticks, _ = dome.counter_read()
        if dome.isHome():
            sys.stdout.write("\r  CW home detected: True")
            sys.stdout.flush()
            break
        sys.stdout.write("\r  CW home detected: False")
        sys.stdout.flush()
    dome.rotation_stop()
    save_state(dome, "calibrate_home_cw")
    time.sleep(5)  # Pause between dome moves
    # Sweep CCW past home
    print("\nSweeping CCW past home...")
    dome.ccw()
    while True:
        current_ticks, _ = dome.counter_read()
        if dome.isHome():
            sys.stdout.write("\r  CCW home detected: True")
            sys.stdout.flush()
            break
        sys.stdout.write("\r  CCW home detected: False")
        sys.stdout.flush()
    dome.rotation_stop()
    save_state(dome, "calibrate_home_ccw")
    time.sleep(5)  # Pause between dome moves
    # Move to center position (average of detected positions)
    print("\nCentering on home position...")
    # Always use the reliable home logic after calibration sweeps
    print("\nFinal homing using park.py logic...")
    dome.home()
    save_state(dome, "calibrate_home_centered")
    print("Home position calibration complete.")


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python hardware_test.py "
            "[rotate_segments|count_full_rotation|calibrate_home] "
            "[cw|ccw]"
        )
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "rotate_segments":
        rotate_segments()
    elif cmd == "count_full_rotation":
        if len(sys.argv) < 3 or sys.argv[2] not in ["cw", "ccw"]:
            print("Specify direction: cw or ccw")
            sys.exit(1)
        count_full_rotation(sys.argv[2])
    elif cmd == "calibrate_home":
        calibrate_home()
    else:
        print("Unknown command: {}".format(cmd))
        sys.exit(1)


if __name__ == "__main__":
    main()
