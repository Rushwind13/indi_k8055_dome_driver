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


# --- Shared helpers ---
def abort():
    print("Test failed. Aborting...")
    import subprocess

    subprocess.call(
        [sys.executable, os.path.join(os.path.dirname(__file__), "../scripts/abort.py")]
    )
    sys.exit(1)


def telemetry(stage, start_pos, start_ticks, end_pos, end_ticks, split, elapsed):
    print(
        "{}: From={:.2f}deg, Cur={:.2f}deg, "
        "Start tics={}, "
        "Cur tics={}, Split={:.2f}s, Total={:.2f}s".format(
            stage, start_pos, end_pos, start_ticks, end_ticks, split, elapsed
        )
    )


def move_ticks(dome, direction, ticks, label, detect_home=False, print_interval=10):
    if direction == "cw":
        dome.cw()
    else:
        dome.ccw()
    t0 = time.time()
    start_pos = dome.get_pos()
    start_ticks, _ = dome.counter_read()
    home_detected = False
    last_cardinal_time = t0
    last_cardinal = None
    while True:
        encoder_ticks, _ = dome.counter_read()
        current_pos = dome.current_position()
        cardinal = int(round(current_pos / 45.0)) * 45 % 360
        # Only print if within 1 degree of
        # the cardinal point to avoid missing due to rounding
        if abs((current_pos - cardinal) % 360.0) < 1.0:
            if last_cardinal != cardinal:
                now = time.time()
                telemetry(
                    "{} @ {} deg ".format(label, cardinal),
                    start_pos,
                    start_ticks,
                    current_pos,
                    encoder_ticks,
                    now - last_cardinal_time,
                    now - t0,
                )
                last_cardinal_time = now
                last_cardinal = cardinal
        if detect_home and dome.isHome():
            home_detected = True
            break
        if encoder_ticks >= ticks:
            break
        time.sleep(0.1)
    final_pos, final_ticks = dome.rotation_stop()
    time.sleep(1)
    t1 = time.time()
    telemetry(
        label + " (final)",
        start_pos,
        start_ticks,
        final_pos,
        final_ticks,
        t1 - last_cardinal_time,
        t1 - t0,
    )
    return home_detected, encoder_ticks


def rotate_segments():
    """
    Rotate dome one full revolution in 8 segments (45 deg each)
    """
    dome = Dome()
    restore_state(dome)
    print("Starting segmented rotation test...")
    for i, tics in enumerate(SEGMENT_TICS):
        print("Segment {}: Rotating {} tics".format(i + 1, tics))
        move_ticks(dome, "cw", tics, "Segment {}".format(i + 1), detect_home=False)
        print("  Done.")
        save_state(dome, "rotate_segments")
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
    t0 = time.time()
    start_pos, start_ticks = dome.home()
    time.sleep(5)
    if not dome.isHome():
        abort()
    t1 = time.time()
    cur_pos = dome.get_pos()
    cur_ticks, _ = dome.counter_read()
    telemetry("Home", start_pos, start_ticks, cur_pos, cur_ticks, t1 - t0, t1 - t0)
    save_state(dome, "count_full_rotation_home")

    # Start rotation and ignore home until safety tics have elapsed
    print("Starting full rotation...")
    if direction.lower() == "cw":
        dome.cw()
    else:
        dome.ccw()
    t0 = time.time()
    start_pos = dome.get_pos()
    start_ticks, _ = dome.counter_read()
    safety_tics = 20  # Minimum tics before checking for home
    home_detected = False
    max_tics = 500  # Safety max
    last_cardinal_time = t0
    last_cardinal = None
    while True:
        encoder_ticks, _ = dome.counter_read()
        current_pos = dome.current_position()
        cardinal = int(round(current_pos / 45.0)) * 45 % 360
        if abs((current_pos - cardinal) % 360.0) < 1.0:
            if last_cardinal != cardinal:
                now = time.time()
                telemetry(
                    "Rotating @ {} deg ".format(cardinal),
                    start_pos,
                    start_ticks,
                    current_pos,
                    encoder_ticks,
                    now - last_cardinal_time,
                    now - t0,
                )
                last_cardinal_time = now
                last_cardinal = cardinal
        if encoder_ticks >= safety_tics:
            if dome.isHome():
                home_detected = True
                break
        if encoder_ticks >= max_tics:
            print("Safety max tics reached, aborting!")
            break
        time.sleep(0.1)
    final_pos, final_ticks = dome.rotation_stop()
    time.sleep(1)
    t1 = time.time()
    telemetry(
        "Rotating (final)",
        start_pos,
        start_ticks,
        final_pos,
        final_ticks,
        t1 - last_cardinal_time,
        t1 - t0,
    )
    if not home_detected:
        print("Home not detected after full revolution!")
        abort()
    print("\nTotal tics for full revolution: {}".format(final_ticks))
    # Log delta between measured and configured values
    if direction.lower() == "cw":
        configured_tics = dome.encoder_tics_per_dome_revolution[dome.CW]
    else:
        configured_tics = dome.encoder_tics_per_dome_revolution[dome.CCW]
    delta = final_ticks - configured_tics
    print("Configured tics for {}: {}".format(direction.upper(), configured_tics))
    print("Delta (measured - configured): {}".format(delta))
    save_state(dome, "count_full_rotation")


def calibrate_home():
    # 1) Move to home first. If can't get there, fail.
    print("Moving to home position...")
    t0 = time.time()

    dome = Dome()
    restore_state(dome)

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
        "Home",
        start_pos,
        start_ticks,
        dome.get_pos(),
        dome.counter_read()[0],
        t1 - t0,
        t1 - t0,
    )

    # 2) Move 20 tics CCW away from home
    print("Moving 20 tics CCW away from home...")
    move_ticks(dome, "ccw", 20, "CCW Away", detect_home=False)

    # 3) Sweep through home CW (40 tics), detect home. If not detected, fail.
    print("Sweeping CW through home (40 tics)...")
    home_detected, _ = move_ticks(dome, "cw", 40, "CW Sweep", detect_home=True)
    if not home_detected:
        abort()

    # 4) Sweep through home CCW (40 tics), detect home. If not detected, fail.
    print("Sweeping CCW through home (40 tics)...")
    home_detected, _ = move_ticks(dome, "ccw", 40, "CCW Sweep", detect_home=True)
    if not home_detected:
        abort()

    # 5) Repeat sweeps two more times
    for i in range(2):
        print("Repeat CW sweep {}...".format(i + 2))
        home_detected, _ = move_ticks(
            dome, "cw", 40, "CW Sweep {}".format(i + 2), detect_home=True
        )
        if not home_detected:
            abort()
        print("Repeat CCW sweep {}...".format(i + 2))
        home_detected, _ = move_ticks(
            dome, "ccw", 40, "CCW Sweep {}".format(i + 2), detect_home=True
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
    final_ticks, _ = dome.counter_read()
    telemetry(
        "Final Home",
        dome.get_pos(),
        start_ticks,
        dome.get_pos(),
        final_ticks,
        t1 - t0,
        t1 - t0,
    )
    if abs(final_ticks) > 2:
        print("Unexpected encoder ticks after homing: {}".format(final_ticks))
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
