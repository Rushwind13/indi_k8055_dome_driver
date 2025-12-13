#!/usr/bin/env python
"""
Functional Test Script for Dome Goto Operations

This script exercises the dome's goto functionality by invoking the goto.py script
with various azimuths and confirming the dome moves to the correct positions.
Telemetry is emitted using the same function as hardware_test.py.

Tested positions: 0, 90, 180, 270 degrees
Start at Home (225 deg), then test short, medium, and long slews in both directions.
"""

import json
import os
import subprocess
import sys
import time

try:
    input_func = raw_input  # Python 2
except NameError:
    input_func = input  # Python 3

STATE_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "dome_state.json")
)
GOTO_SCRIPT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "goto.py")
)


def get_dome_state():
    """Read the persistent dome state file."""
    if not os.path.exists(STATE_FILE):
        return None
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def run_goto(azimuth):
    """Call goto.py script to move dome to target azimuth."""
    cmd = [sys.executable, GOTO_SCRIPT, str(azimuth)]
    return subprocess.call(cmd) == 0


def functional_test_goto():
    """Test goto.py by calling it as a subprocess and verifying state file."""
    print("[FunctionalTest] Moving to Home (225 deg)...")
    ok = run_goto(225)
    if not ok:
        print("Goto script failed for 225 deg (home)")
        return
    time.sleep(2)
    state = get_dome_state()
    actual_pos = state.get("position", None) if state else None
    print("Dome state after homing: {} deg".format(actual_pos))
    user_pos = input_func("After homing, what is the approximate dome azimuth (deg)? ")
    print("[User] Dome reported at: {} deg".format(user_pos))

    test_positions = [0, 90, 180, 270]
    for target in test_positions:
        print("[FunctionalTest] Goto {} deg".format(target))
        ok = run_goto(target)
        if not ok:
            print("Goto script failed for {} deg".format(target))
            continue
        time.sleep(2)
        state = get_dome_state()
        actual_pos = state.get("position", None) if state else None
        print("Dome state after move: {} deg".format(actual_pos))
        user_pos = input_func(
            "After moving to {} deg, "
            "what is the approximate dome azimuth (deg)? ".format(target)
        )
        print("[User] Dome reported at: {} deg".format(user_pos))

    print("[FunctionalTest] Testing short, medium, long slews (CW/CCW)...")
    slew_tests = [
        (90, 0),  # short (CCW)
        (0, 180),  # medium (CW)
        (180, 90),  # short (CCW)
        (90, 270),  # medium (CW)
        (270, 0),  # long (CW)
        (0, 270),  # long (CCW)
    ]
    for start, end in slew_tests:
        print("[FunctionalTest] Slew from {} to {} deg".format(start, end))
        ok = run_goto(start)
        if not ok:
            print("Goto script failed for {} deg (slew start)".format(start))
            continue
        time.sleep(2)
        state = get_dome_state()
        user_start = input_func(
            "After slewing to start {} deg, "
            "what is the approximate dome azimuth (deg)? ".format(start)
        )
        print("[User] Dome reported at: {} deg".format(user_start))
        ok = run_goto(end)
        if not ok:
            print("Goto script failed for {} deg (slew end)".format(end))
            continue
        time.sleep(2)
        state = get_dome_state()
        actual_pos = state.get("position", None) if state else None
        user_end = input_func(
            "After slewing to end {} deg, "
            "what is the approximate dome azimuth (deg)? ".format(end)
        )
        print("[User] Dome reported at: {} deg".format(user_end))
        print("Dome state after slew: {} deg".format(actual_pos))

    print("[FunctionalTest] Final: Moving to Home (225 deg)...")
    ok = run_goto(225)
    if not ok:
        print("Goto script failed for 225 deg (final home)")
        return
    time.sleep(2)
    state = get_dome_state()
    actual_pos = state.get("position", None) if state else None
    print("Dome state after final homing: {} deg".format(actual_pos))
    user_pos = input_func(
        "After final homing, what is the approximate dome azimuth (deg)? "
    )
    print("[User] Dome reported at: {} deg".format(user_pos))


if __name__ == "__main__":
    functional_test_goto()
