#!/usr/bin/env python
"""
Functional Test Script for Dome Goto Operations

This script exercises the dome's goto functionality by invoking the goto.py script
with various azimuths and confirming the dome moves to the correct positions.
Telemetry is emitted using the same function as hardware_test.py.

Tested positions: 0, 90, 180, 270 degrees
Start at Home (225 deg), then test short, medium, and long slews in both directions.
"""

try:
    input_func = raw_input  # Python 2
except NameError:
    input_func = input  # Python 3

import os
import subprocess
import sys
import time

from dome import Dome
from hardware_test import telemetry
from persistence import restore_state, save_state

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib")
)

GOTO_SCRIPT = os.path.join(os.path.dirname(__file__), "../../scripts/goto.py")


# Helper to run goto.py and wait for completion


def run_goto(azimuth):
    lib_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lib"))
    env = os.environ.copy()
    env["PYTHONPATH"] = lib_dir + (
        os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else ""
    )
    cmd = [sys.executable, GOTO_SCRIPT, str(azimuth)]
    result = subprocess.call(cmd, env=env)
    return result == 0


def functional_test_goto():
    dome = Dome()
    restore_state(dome)
    print("[FunctionalTest] Moving to Home (225 deg)...")
    t0 = time.time()
    start_pos, start_ticks = dome.home()
    save_state(dome, "goto_home")

    time.sleep(2)
    cur_pos = dome.current_position()
    cur_ticks, _ = dome.counter_read()
    t1 = time.time()
    telemetry("Start at Home", start_pos, start_ticks, cur_pos, cur_ticks, t1 - t0, 0)
    user_pos = input_func("After homing, what is the approximate dome azimuth (deg)? ")
    print("[User] Dome reported at: {} deg".format(user_pos))

    test_positions = [0, 90, 180, 270]
    for target in test_positions:
        print("[FunctionalTest] Goto {} deg".format(target))
        t2 = time.time()
        ok = run_goto(target)
        if not ok:
            print("Goto script failed for {} deg".format(target))
            continue
        time.sleep(5)
        cur_pos = dome.current_position()
        cur_ticks, _ = dome.counter_read()
        telemetry(
            "Goto {}".format(target),
            start_pos,
            start_ticks,
            cur_pos,
            cur_ticks,
            time.time() - t2,
            time.time() - t1,
        )
        user_pos = input_func(
            "After moving to {} deg, "
            "what is the approximate dome azimuth (deg)? ".format(target)
        )
        print("[User] Dome reported at: {} deg".format(user_pos))
        start_pos = cur_pos
        start_ticks = cur_ticks
        save_state(dome, "goto_{}".format(target))

    # Test short, medium, long slews in both directions
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
        # Move to start
        ok = run_goto(start)
        if not ok:
            print("Goto script failed for {} deg (slew start)".format(start))
            continue
        time.sleep(2)
        s_pos = dome.current_position()
        s_ticks, _ = dome.counter_read()
        user_start = input_func(
            "After slewing to start {} deg, "
            "what is the approximate dome azimuth (deg)? ".format(start)
        )
        print("[User] Dome reported at: {} deg".format(user_start))
        t2 = time.time()
        time.sleep(2)
        e_pos = dome.current_position()
        e_ticks, _ = dome.counter_read()
        telemetry(
            "Slew {}->{}".format(start, end),
            s_pos,
            s_ticks,
            e_pos,
            e_ticks,
            time.time() - t2,
            time.time() - t1,
        )
        user_end = input_func(
            "After slewing to end {} deg, "
            "what is the approximate dome azimuth (deg)? ".format(end)
        )
        print("[User] Dome reported at: {} deg".format(user_end))
    start_pos, start_ticks = dome.home()
    save_state(dome, "goto_home")

    time.sleep(2)
    cur_pos = dome.current_position()
    cur_ticks, _ = dome.counter_read()
    t3 = time.time()
    telemetry(
        "End at Home", start_pos, start_ticks, cur_pos, cur_ticks, t3 - t2, t2 - t1
    )
    user_pos = input_func(
        "After final homing, what is the approximate dome azimuth (deg)? "
    )
    print("[User] Dome reported at: {} deg".format(user_pos))


if __name__ == "__main__":
    functional_test_goto()
