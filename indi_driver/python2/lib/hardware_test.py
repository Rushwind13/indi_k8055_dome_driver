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
    # Move dome away from home to ensure physical movement
    print("Moving dome away from home position before calibration...")
    if dome.isHome():
        dome.ccw()
        away_ticks = 40  # Move ~45 degrees away
        moved = 0
        while moved < away_ticks:
            current_ticks, _ = dome.counter_read()
            moved = abs(current_ticks)
            sys.stdout.write("\r  Moving away: {} tics".format(moved))
            sys.stdout.flush()
        dome.rotation_stop()
        time.sleep(2)
        print("Dome moved away from home.")

    # Sweep CW past home and record all transitions
    print("Sweeping CW past home and recording transitions...")
    dome.cw()
    home_zone_start = None
    home_zone_end = None
    last_home = False
    transitions = []
    while True:
        current_ticks, _ = dome.counter_read()
        is_home = dome.isHome()
        if is_home and not last_home:
            home_zone_start = current_ticks
            transitions.append((current_ticks, "enter"))
        if not is_home and last_home:
            home_zone_end = current_ticks
            transitions.append((current_ticks, "exit"))
        last_home = is_home
        sys.stdout.write("\r  CW home: {} tick: {}".format(is_home, current_ticks))
        sys.stdout.flush()
        # Stop after passing through home zone and exiting
        if home_zone_start is not None and home_zone_end is not None:
            break
    dome.rotation_stop()
    save_state(dome, "calibrate_home_cw")
    time.sleep(5)

    # Sweep CCW past home and record all transitions
    print("\nSweeping CCW past home and recording transitions...")
    dome.ccw()
    home_zone_start_ccw = None
    home_zone_end_ccw = None
    last_home = False
    transitions_ccw = []
    while True:
        current_ticks, _ = dome.counter_read()
        is_home = dome.isHome()
        if is_home and not last_home:
            home_zone_start_ccw = current_ticks
            transitions_ccw.append((current_ticks, "enter"))
        if not is_home and last_home:
            home_zone_end_ccw = current_ticks
            transitions_ccw.append((current_ticks, "exit"))
        last_home = is_home
        sys.stdout.write("\r  CCW home: {} tick: {}".format(is_home, current_ticks))
        sys.stdout.flush()
        # Stop after passing through home zone and exiting
        if home_zone_start_ccw is not None and home_zone_end_ccw is not None:
            break
    dome.rotation_stop()
    save_state(dome, "calibrate_home_ccw")
    time.sleep(5)

    # Calculate home zone width and center
    print("\nCalculating home zone width and center...")
    if home_zone_start is not None and home_zone_end is not None:
        width_cw = abs(home_zone_end - home_zone_start)
        center_cw = (home_zone_start + home_zone_end) / 2.0
        print(
            "CW sweep: Home zone width: {} tics, center: {:.1f}".format(
                width_cw, center_cw
            )
        )
    else:
        print("CW sweep: Could not determine home zone width.")
        width_cw = None
        center_cw = None
    if home_zone_start_ccw is not None and home_zone_end_ccw is not None:
        width_ccw = abs(home_zone_end_ccw - home_zone_start_ccw)
        center_ccw = (home_zone_start_ccw + home_zone_end_ccw) / 2.0
        print(
            "CCW sweep: Home zone width: {} tics, center: {:.1f}".format(
                width_ccw, center_ccw
            )
        )
    else:
        print("CCW sweep: Could not determine home zone width.")
        width_ccw = None
        center_ccw = None

    # Move dome to average center of both sweeps if possible
    print("\nMoving dome to center of home zone...")
    if center_cw is not None and center_ccw is not None:
        final_center = (center_cw + center_ccw) / 2.0
        print("Moving to tick position: {:.1f}".format(final_center))
        dome.rotation(final_center)
    elif center_cw is not None:
        print("Moving to tick position (CW center): {:.1f}".format(center_cw))
        dome.rotation(center_cw)
    elif center_ccw is not None:
        print("Moving to tick position (CCW center): {:.1f}".format(center_ccw))
        dome.rotation(center_ccw)
    else:
        print("Could not determine home zone center; using home().")
        dome.home()
    save_state(dome, "calibrate_home_centered")
    print("\nHome position calibration complete.")
    print("CW transitions: {}".format(transitions))
    print("CCW transitions: {}".format(transitions_ccw))


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
