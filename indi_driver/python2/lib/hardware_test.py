#!/usr/bin/env python
"""
Refactored hardware test for dome rotation and calibration.
All helpers and test functions are top-level. CLI and persistence are robust.
"""

import json
import os
import sys
import time

from dome import Dome


def Telemetry(context):
    Telemetry_short(context)


def Telemetry_short(context):
    print(
        "  {:06.3f}: Digital inputs 54321: {} tics: {} {} homes: {}".format(
            context["run_time"],
            bin(context["digital_mask"])[2:].zfill(5)
            if context["digital_mask"] is not None
            else "N/A",
            context["encoder_ticks"],
            context["home_ticks"],
            context["homes"],
        )
    )


def Telemetry_long(context):
    enc_state = context["dome"].read_encoder_state()
    print("Telemetry:")
    print("  Run time: {:06.3f} sec".format(context["run_time"]))
    print("  Position: {}".format(context["position"]))
    print("  Encoders: {}".format(context["encoders"]))
    print("  Gray code: {}".format(enc_state))
    print(
        "  Rotation Direction: {}".format(
            context["dome"].detect_encoder_direction(enc_state)
        )
    )
    print("  Home Switch: {}".format(context["home_switch"]))
    print("  Homes: {}".format(context["homes"]))
    print(
        "  Digital input bitmask: {}".format(
            bin(context["digital_mask"])[2:].zfill(5)
            if context["digital_mask"] is not None
            else "N/A"
        )
    )
    print("  is_turning: {}".format(context["dome"].is_turning))
    print("  Direction: {}".format(context["dome"].direction_str()))
    print("---")


def test_rotation(
    dome,
    direction_name,
    rotation_func,
    rotation_amount=None,
    max_duration=None,
    stop_at_home=True,
    min_homes=5,
    use_ticks=True,
):
    """
    Parameterized rotation test function.

    Args:
        dome: Dome object to test
        direction_name: String name of direction ("CW" or "CCW")
        rotation_func: Function to call to start rotation (dome.cw or dome.ccw)
        rotation_amount: Amount to rotate (encoder ticks if use_ticks, else seconds)
        max_duration: Maximum test duration in seconds (safety timeout, optional)
        stop_at_home: Whether to stop at home switch
        min_homes: Minimum number of home passes before stopping (if stop_at_home=True)
        use_ticks: If True, rotation_amount is in encoder ticks; if False, in seconds

    Returns:
        tuple: (elapsed_time, home_count, total_encoder_ticks)
    """
    if rotation_amount is None and max_duration is None:
        raise ValueError("Must specify either rotation_amount or max_duration")

    limit_type = "ticks" if use_ticks and rotation_amount is not None else "time"
    limit_value = (
        rotation_amount if use_ticks and rotation_amount is not None else max_duration
    )

    print(
        "Starting {} rotation test ({} limit: {})...".format(
            direction_name, limit_type, limit_value
        )
    )

    rotation_func()
    start_time = time.time()
    poll_interval = getattr(dome, "POLL", 0.2)
    dome.homes_reset()

    run_time = 0
    homes = 0
    total_ticks = 0
    home_tics = 0
    prev_home_switch = False

    try:
        while True:
            position = dome.get_pos()
            encoder_ticks, home_ticks = dome.counter_read()
            total_ticks = encoder_ticks
            encoders = (dome.dome.digital_in(dome.A), dome.dome.digital_in(dome.B))
            home_switch = dome.dome.digital_in(dome.HOME)
            digital_mask = (
                dome.dome.read_all_digital()
                if hasattr(dome.dome, "read_all_digital")
                else None
            )

            # Use existing Telemetry function for output, now with prev_home_switch
            Telemetry(
                {
                    "run_time": run_time,
                    "dome": dome,
                    "position": position,
                    "encoder_ticks": encoder_ticks,
                    "home_ticks": home_ticks,
                    "encoders": encoders,
                    "home_switch": home_switch,
                    "digital_mask": digital_mask,
                    "homes": homes,
                    "home_tics": home_tics,
                    "prev_home_switch": prev_home_switch,
                }
            )

            # Count home tics and transitions
            if home_switch:
                home_tics += 1
                if not prev_home_switch:
                    homes += 1
            prev_home_switch = home_switch

            # Check rotation limit
            if use_ticks and rotation_amount is not None:
                if total_ticks >= rotation_amount:
                    print("Target encoder ticks ({}) reached.".format(rotation_amount))
                    break
            elif max_duration is not None:
                if run_time >= max_duration:
                    print("Maximum duration ({:.1f}s) reached.".format(max_duration))
                    break

            # Safety timeout if max_duration specified
            if max_duration is not None and run_time >= max_duration:
                print("Safety timeout reached ({:.1f}s).".format(max_duration))
                break

            time.sleep(poll_interval)
            run_time = time.time() - start_time
    finally:
        dome.rotation_stop()
        print("Test complete. Dome stopped.")
        print("  Total encoder ticks: {}".format(total_ticks))
        print("  Total home tics: {}".format(home_tics))
        print("  Home transitions: {}".format(homes))
        print("  Time for {} rotation: {:.2f} seconds".format(direction_name, run_time))

    return run_time, homes, total_ticks, home_tics


def full_rotation_test(dome, max_duration=180, direction="CW"):
    print("\n=== FULL ROTATION TEST ===")
    # Ensure at home
    if not dome.isHome():
        print("Moving to home position...")
        dome.home()
        time.sleep(2)
    dome.encoder_reset()
    print("Starting full rotation {}...".format(direction))
    if direction.upper() == "CCW":
        dome.ccw()
    else:
        dome.cw()
    start_time = time.time()
    left_home = False
    left_home_tick = None
    prev_home_switch = dome.isHome()
    last_telemetry_tick = 0
    while True:
        encoder_ticks, home_ticks = dome.counter_read()
        home_switch = dome.dome.digital_in(dome.HOME)
        # Telemetry every 10 encoder ticks
        if encoder_ticks - last_telemetry_tick >= 10 or encoder_ticks == 0:
            Telemetry(
                {
                    "run_time": time.time() - start_time,
                    "dome": dome,
                    "position": dome.get_pos(),
                    "encoder_ticks": encoder_ticks,
                    "home_ticks": home_ticks,
                    "encoders": (
                        dome.dome.digital_in(dome.A),
                        dome.dome.digital_in(dome.B),
                    ),
                    "home_switch": home_switch,
                    "digital_mask": dome.dome.read_all_digital()
                    if hasattr(dome.dome, "read_all_digital")
                    else None,
                    "homes": None,
                    "home_tics": None,
                    "prev_home_switch": prev_home_switch,
                }
            )
            last_telemetry_tick = encoder_ticks
        # Wait until we've left home at least once
        if not left_home and not home_switch and prev_home_switch:
            left_home = True
            left_home_tick = encoder_ticks
        # Only finish after we've left home,
        # moved at least 2 encoder ticks, and
        # then returned
        if left_home and left_home_tick is not None:
            if abs(encoder_ticks - left_home_tick) > 1:
                if home_switch and not prev_home_switch:
                    print("Returned to home pos after moving more than 1 encoder tic.")
                    break
        if time.time() - start_time > max_duration:
            print("Timeout reached.")
            break
        prev_home_switch = home_switch
        time.sleep(0.05)
    dome.rotation_stop()
    elapsed = time.time() - start_time
    encoder_ticks, _ = dome.counter_read()
    print("Full rotation: {} ticks, {:.2f} seconds".format(encoder_ticks, elapsed))
    return encoder_ticks, elapsed


def calibrate_home_width(dome, max_duration=60):
    print("\n=== HOME WIDTH CALIBRATION (bidirectional, 3x) ===")

    def cross_home(direction_func, leave_func, label, sweep_ticks=50):
        if dome.isHome():
            print("Moving off home ({} for non-home)...".format(label))
            leave_func()
            t0 = time.time()
            while dome.isHome() and (time.time() - t0 < max_duration / 3.0):
                time.sleep(0.05)
            dome.rotation_stop()
            time.sleep(0.2)
        print(
            "Sweeping across home region ({} direction, {} ticks)...".format(
                label, sweep_ticks
            )
        )
        dome.encoder_reset()
        direction_func()
        in_home = False
        home_start_tick = None
        home_end_tick = None
        t0 = time.time()
        home_tics = 0
        not_to_home = 0
        home_to_not = 0
        prev_home_switch = False
        first_home_tick = None
        last_home_tick = None
        while True:
            encoder_ticks, _ = dome.counter_read()
            home_switch = dome.dome.digital_in(dome.HOME)
            # Count home tics and both transitions
            if home_switch:
                home_tics += 1
                if not prev_home_switch:
                    not_to_home += 1
                    if not in_home:
                        home_start_tick = encoder_ticks
                        in_home = True
                if first_home_tick is None:
                    first_home_tick = encoder_ticks
                last_home_tick = encoder_ticks
            else:
                if prev_home_switch:
                    home_to_not += 1
                    if in_home:
                        home_end_tick = encoder_ticks
                        in_home = False
            prev_home_switch = home_switch
            # Telemetry for each tick, now with both transitions
            Telemetry(
                {
                    "run_time": time.time() - t0,
                    "dome": dome,
                    "position": dome.get_pos(),
                    "encoder_ticks": encoder_ticks,
                    "home_ticks": None,
                    "encoders": (
                        dome.dome.digital_in(dome.A),
                        dome.dome.digital_in(dome.B),
                    ),
                    "home_switch": home_switch,
                    "digital_mask": dome.dome.read_all_digital()
                    if hasattr(dome.dome, "read_all_digital")
                    else None,
                    "homes": not_to_home,
                    "home_tics": home_tics,
                    "prev_home_switch": prev_home_switch,
                    "not_to_home": not_to_home,
                    "home_to_not": home_to_not,
                }
            )
            # End sweep after double sweep_ticks
            if abs(encoder_ticks) >= sweep_ticks * 2:
                break
            if time.time() - t0 > max_duration / 2.0:
                print("Timeout sweeping home ({}).".format(label))
                break
            time.sleep(0.02)
        dome.rotation_stop()
        time.sleep(0.2)
        print(
            "Home: {} to {} ({}), home tics: {}, not->home: {}, home->not: {}".format(
                home_start_tick,
                home_end_tick,
                label,
                home_tics,
                not_to_home,
                home_to_not,
            )
        )
        print(
            "First home tick: {} | Last home tick: {} | Total sweep ticks: {}".format(
                first_home_tick, last_home_tick, abs(encoder_ticks)
            )
        )
        return (
            home_start_tick,
            home_end_tick,
            home_tics,
            not_to_home,
            home_to_not,
            first_home_tick,
            last_home_tick,
            abs(encoder_ticks),
        )

    home_widths = []
    home_tics_list = []
    not_to_home_list = []
    home_to_not_list = []
    sweep_ticks = 50
    for i in range(3):
        print("\nPass {}: CW across home".format(i + 1))
        cw_results = cross_home(dome.cw, dome.ccw, "CW", sweep_ticks)
        print("Pass {}: CCW across home".format(i + 1))
        ccw_results = cross_home(dome.ccw, dome.cw, "CCW", sweep_ticks)
        (
            cw_start,
            cw_end,
            cw_tics,
            cw_n2h,
            cw_h2n,
            cw_first,
            cw_last,
            cw_total,
        ) = cw_results
        (
            ccw_start,
            ccw_end,
            ccw_tics,
            ccw_n2h,
            ccw_h2n,
            ccw_first,
            ccw_last,
            ccw_total,
        ) = ccw_results
        if cw_start is not None and cw_end is not None:
            home_widths.append(abs(cw_end - cw_start))
            home_tics_list.append(cw_tics)
            not_to_home_list.append(cw_n2h)
            home_to_not_list.append(cw_h2n)
        if ccw_start is not None and ccw_end is not None:
            home_widths.append(abs(ccw_end - ccw_start))
            home_tics_list.append(ccw_tics)
            not_to_home_list.append(ccw_n2h)
            home_to_not_list.append(ccw_h2n)
        print(
            "CW sweep: first home tick {}, last home tick {}, total sweep {}".format(
                cw_first, cw_last, cw_total
            )
        )
        print(
            "CCW sweep: first home tick {}, last home tick {}, total sweep {}".format(
                ccw_first, ccw_last, ccw_total
            )
        )

    if home_widths:
        avg_width = int(round(sum(home_widths) / float(len(home_widths))))
        avg_tics = (
            int(round(sum(home_tics_list) / float(len(home_tics_list))))
            if home_tics_list
            else 0
        )
        avg_n2h = (
            float(sum(not_to_home_list)) / len(not_to_home_list)
            if not_to_home_list
            else 0
        )
        avg_h2n = (
            float(sum(home_to_not_list)) / len(home_to_not_list)
            if home_to_not_list
            else 0
        )
        print("\nAverage home width (encoder ticks): {}".format(avg_width))
        print("Average home tics (samples while home): {}".format(avg_tics))
        print("Average not->home transitions: {:.2f}".format(avg_n2h))
        print("Average home->not transitions: {:.2f}".format(avg_h2n))
        last_start = ccw_start if ccw_start is not None else cw_start
        last_end = ccw_end if ccw_end is not None else cw_end
        if last_start is not None and last_end is not None:
            midpoint = last_start + (last_end - last_start) // 2
            print("Moving to midpoint of last home region: {}".format(midpoint))
            dome.encoder_reset()
            dome.cw() if midpoint >= 0 else dome.ccw()
            while True:
                encoder_ticks, _ = dome.counter_read()
                if (midpoint >= 0 and encoder_ticks >= midpoint) or (
                    midpoint < 0 and encoder_ticks <= midpoint
                ):
                    break
                time.sleep(0.02)
            dome.rotation_stop()
            print("Dome positioned at home midpoint.")
            return avg_width, midpoint, avg_tics, avg_n2h, avg_h2n
    print("Failed to calibrate home width.")
    return None, None, None, None, None


def standard_rotation_test(dome, state_file):
    FULL_ROTATION_TICKS = 314
    DEGREES_PER_STEP = 45
    TICKS_PER_STEP = [39, 39, 39, 40] * 2
    NUM_STEPS = len(TICKS_PER_STEP)
    MAX_SAFETY_TIMEOUT = 300
    stop_at_home = False
    min_homes_before_stop = 5

    print("Configuration:")
    print("  Full rotation: {} ticks".format(FULL_ROTATION_TICKS))
    print("  Steps: {} x {} degrees".format(NUM_STEPS, DEGREES_PER_STEP))
    print("  Ticks per step: {}".format(TICKS_PER_STEP))
    print("")

    total_cwtime = 0
    total_cwhomes = 0
    total_cwticks = 0

    for step in range(NUM_STEPS):
        print("\n--- CW Rotation Step {}/{} ---".format(step + 1, NUM_STEPS))
        cwtime, cwhomes, cwticks = test_rotation(
            dome=dome,
            direction_name="CW",
            rotation_func=dome.cw,
            rotation_amount=TICKS_PER_STEP[step],
            max_duration=MAX_SAFETY_TIMEOUT,
            stop_at_home=stop_at_home,
            min_homes=min_homes_before_stop,
            use_ticks=True,
        )
        total_cwtime += cwtime
        total_cwhomes += cwhomes
        total_cwticks += cwticks
        print(
            "Step {} complete. Position: {:.1f} degrees".format(
                step + 1, dome.get_pos()
            )
        )
        with open(state_file, "w") as f:
            json.dump({"position": dome.get_pos()}, f)
        time.sleep(5)

    print("\n" + "=" * 50)
    print("ROTATION TEST SUMMARY")
    print("=" * 50)
    print("CW Rotation ({} steps x {} degrees):".format(NUM_STEPS, DEGREES_PER_STEP))
    print("  Home switches: {}".format(total_cwhomes))
    print("  Encoder ticks: {}".format(total_cwticks))
    print("  Time: {:.2f} seconds".format(total_cwtime))
    print("  Final position: {:.1f} degrees".format(dome.get_pos()))
    print("")
    print("=" * 50)


def main():
    state_file = "dome_state.json"
    dome = Dome()
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            state = json.load(f)
        dome.position = state.get("position", dome.HOME_POS)
        print("Loaded persistent dome position: {:.1f}".format(dome.position))

    # CLI arg/env var selection
    # Usage: python hardware_test.py [test] [direction]
    # test: 1=standard, 2=full rotation, 3=home width
    # direction: CW or CCW (only for test 2)
    test_choice = os.environ.get("DOME_TEST", None)
    direction = os.environ.get("DOME_DIRECTION", None)
    if len(sys.argv) > 1:
        test_choice = sys.argv[1]
    if len(sys.argv) > 2:
        direction = sys.argv[2]
    if not test_choice:
        test_choice = "1"
    if not direction:
        direction = "CW"

    print("Test selection: {}".format(test_choice))
    if test_choice == "2":
        print("Full rotation direction: {}".format(direction))
        full_rotation_test(dome, direction=direction)
        with open(state_file, "w") as f:
            json.dump({"position": dome.get_pos()}, f)
        return
    elif test_choice == "3":
        calibrate_home_width(dome)
        with open(state_file, "w") as f:
            json.dump({"position": dome.get_pos()}, f)
        return
    else:
        standard_rotation_test(dome, state_file)


if __name__ == "__main__":
    main()
