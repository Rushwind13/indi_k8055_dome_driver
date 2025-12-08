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
    import subprocess

    dome = Dome()
    restore_state(dome)

    def abort():
        print("Calibration failed. Aborting...")
        subprocess.call(
            [
                sys.executable,
                os.path.join(os.path.dirname(__file__), "../scripts/abort.py"),
            ]
        )
        sys.exit(1)

    def telemetry(stage, start_pos, start_ticks, end_pos, end_ticks, elapsed):
        print(
            "{}: Start pos={:.2f}deg, "
            "Start tics={}, End pos={:.2f}deg, "
            "End tics={}, Elapsed={:.2f}s".format(
                stage, start_pos, start_ticks, end_pos, end_ticks, elapsed
            )
        )

    # 1) Move to home first. If can't get there, fail.
    print("Moving to home position...")
    t0 = time.time()
    dome.home()
    time.sleep(5)
    if not dome.isHome():
        abort()
    t1 = time.time()
    start_pos = dome.get_pos()
    start_ticks, _ = dome.counter_read()
    telemetry(
        "Home", start_pos, start_ticks, dome.get_pos(), dome.counter_read()[0], t1 - t0
    )

    # 2) Move a small distance (10 tics) away from home in CCW direction
    print("Moving 10 tics CCW away from home...")
    dome.ccw()
    t0 = time.time()
    start_pos = dome.get_pos()
    start_ticks, _ = dome.counter_read()
    while True:
        encoder_ticks, _ = dome.counter_read()
        if encoder_ticks >= 10:
            break
    dome.rotation_stop()
    time.sleep(5)
    t1 = time.time()
    telemetry(
        "CCW Away", start_pos, start_ticks, dome.get_pos(), encoder_ticks, t1 - t0
    )

    # 3) Sweep through home CW (20 tics at least), detect home. If not detected, fail.
    print("Sweeping CW through home (20 tics)...")
    dome.cw()
    t0 = time.time()
    start_pos = dome.get_pos()
    start_ticks, _ = dome.counter_read()
    home_detected = False
    while True:
        encoder_ticks, _ = dome.counter_read()
        if dome.isHome():
            home_detected = True
        if encoder_ticks >= 20:
            break
    dome.rotation_stop()
    time.sleep(5)
    t1 = time.time()
    telemetry(
        "CW Sweep", start_pos, start_ticks, dome.get_pos(), encoder_ticks, t1 - t0
    )
    if not home_detected:
        abort()

    # 4) Sweep through home CCW (20 tics), detect home. If not detected, fail.
    print("Sweeping CCW through home (20 tics)...")
    dome.ccw()
    t0 = time.time()
    start_pos = dome.get_pos()
    start_ticks, _ = dome.counter_read()
    home_detected = False
    while True:
        encoder_ticks, _ = dome.counter_read()
        if dome.isHome():
            home_detected = True
        if encoder_ticks >= 20:
            break
    dome.rotation_stop()
    time.sleep(5)
    t1 = time.time()
    telemetry(
        "CCW Sweep", start_pos, start_ticks, dome.get_pos(), encoder_ticks, t1 - t0
    )
    if not home_detected:
        abort()

    # 5) Repeat steps 4 and 5 two more times.
    for i in range(2):
        print("Repeat CW sweep {}...".format(i + 2))
        dome.cw()
        t0 = time.time()
        start_pos = dome.get_pos()
        start_ticks, _ = dome.counter_read()
        home_detected = False
        while True:
            encoder_ticks, _ = dome.counter_read()
            if dome.isHome():
                home_detected = True
            if encoder_ticks >= 20:
                break
        dome.rotation_stop()
        time.sleep(5)
        t1 = time.time()
        telemetry(
            "CW Sweep {}".format(i + 2),
            start_pos,
            start_ticks,
            dome.get_pos(),
            encoder_ticks,
            t1 - t0,
        )
        if not home_detected:
            abort()

        print("Repeat CCW sweep {}...".format(i + 2))
        dome.ccw()
        t0 = time.time()
        start_pos = dome.get_pos()
        start_ticks, _ = dome.counter_read()
        home_detected = False
        while True:
            encoder_ticks, _ = dome.counter_read()
            if dome.isHome():
                home_detected = True
            if encoder_ticks >= 20:
                break
        dome.rotation_stop()
        time.sleep(5)
        t1 = time.time()
        telemetry(
            "CCW Sweep {}".format(i + 2),
            start_pos,
            start_ticks,
            dome.get_pos(),
            encoder_ticks,
            t1 - t0,
        )
        if not home_detected:
            abort()

    # 6) Return to home using home(),
    # count the starting and ending tics.
    # If not the expected amount of tics, fail.
    print("Returning to home position...")
    start_ticks, _ = dome.counter_read()
    t0 = time.time()
    dome.home()
    time.sleep(5)
    t1 = time.time()
    end_ticks, _ = dome.counter_read()
    telemetry(
        "Final Home", dome.get_pos(), start_ticks, dome.get_pos(), end_ticks, t1 - t0
    )
    # Check if encoder ticks are as expected (should be near zero)
    if abs(end_ticks) > 2:
        print("Unexpected encoder ticks after homing: {}".format(end_ticks))
        abort()
    print("Home calibration successful.")


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
