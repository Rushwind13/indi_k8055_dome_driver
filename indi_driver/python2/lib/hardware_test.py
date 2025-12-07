#!/usr/bin/env python
"""
Refactored hardware test for dome rotation and calibration.
All helpers and test functions are top-level. CLI and persistence are robust.
"""

import json
import os
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
    telemetry_delay = 0
    homes = 0
    total_ticks = 0

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

            if telemetry_delay > 100:
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
                    }
                )
                telemetry_delay = 0
            telemetry_delay += 1

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

            if home_switch:
                homes += 1
                print(
                    "Home switch activated {} times during {} rotation.".format(
                        homes, direction_name
                    )
                )
                dome.is_home = True
                dome.set_pos(dome.HOME_POS)
                if stop_at_home and homes >= min_homes:
                    break

            time.sleep(poll_interval)
            run_time = time.time() - start_time
    finally:
        dome.rotation_stop()
        print("Test complete. Dome stopped.")
        print("  Total encoder ticks: {}".format(total_ticks))
        print("  Total homes: {}".format(homes))
        print("  Time for {} rotation: {:.2f} seconds".format(direction_name, run_time))

    return run_time, homes, total_ticks


def full_rotation_test(dome, max_duration=180):
    print("\n=== FULL ROTATION TEST ===")
    if not dome.isHome():
        print("Moving to home position...")
        dome.home()
        time.sleep(2)
    dome.encoder_reset()
    print("Starting full rotation CW...")
    dome.cw()
    start_time = time.time()
    home_seen = False
    while True:
        encoder_ticks, home_ticks = dome.counter_read()
        if dome.isHome() and home_seen:
            print("Returned to home position.")
            break
        if dome.isHome():
            home_seen = True
        if time.time() - start_time > max_duration:
            print("Timeout reached.")
            break
        time.sleep(0.05)
    dome.rotation_stop()
    elapsed = time.time() - start_time
    encoder_ticks, _ = dome.counter_read()
    print("Full rotation: {} ticks, {:.2f} seconds".format(encoder_ticks, elapsed))
    return encoder_ticks, elapsed


def calibrate_home_width(dome, max_duration=60):
    print("\n=== HOME WIDTH CALIBRATION (bidirectional, 3x) ===")

    # Helper to move across home region in a direction, return (start_tick, end_tick)
    def cross_home(direction_func, leave_func, label):
        # Move off home if needed
        if dome.isHome():
            print("Moving off home ({} for non-home)...".format(label))
            leave_func()
            t0 = time.time()
            while dome.isHome() and (time.time() - t0 < max_duration / 3.0):
                time.sleep(0.05)
            dome.rotation_stop()
            time.sleep(0.2)
        # Now move into and across home
        print("Crossing home region ({} direction)...".format(label))
        dome.encoder_reset()
        direction_func()
        in_home = False
        home_start_tick = None
        home_end_tick = None
        t0 = time.time()
        while True:
            encoder_ticks, _ = dome.counter_read()
            if dome.isHome():
                if not in_home:
                    home_start_tick = encoder_ticks
                    in_home = True
            else:
                if in_home:
                    home_end_tick = encoder_ticks
                    break
            if time.time() - t0 > max_duration / 3.0:
                print("Timeout crossing home ({}).".format(label))
                break
            time.sleep(0.02)
        dome.rotation_stop()
        time.sleep(0.2)
        return home_start_tick, home_end_tick

    # Perform 3 bidirectional crossings
    home_widths = []
    for i in range(3):
        print("\nPass {}: CW across home".format(i + 1))
        cw_start, cw_end = cross_home(dome.cw, dome.ccw, "CW")
        print("  Home region: {} to {} (CW)".format(cw_start, cw_end))
        print("Pass {}: CCW across home".format(i + 1))
        ccw_start, ccw_end = cross_home(dome.ccw, dome.cw, "CCW")
        print("  Home region: {} to {} (CCW)".format(ccw_start, ccw_end))
        if cw_start is not None and cw_end is not None:
            home_widths.append(abs(cw_end - cw_start))
        if ccw_start is not None and ccw_end is not None:
            home_widths.append(abs(ccw_end - ccw_start))

    # Average width and center
    if home_widths:
        avg_width = int(round(sum(home_widths) / float(len(home_widths))))
        print("\nAverage home width (ticks): {}".format(avg_width))
        # Center: move to midpoint of last crossing
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
            return avg_width, midpoint
    print("Failed to calibrate home width.")
    return None, None


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

    print("\nSelect test to run:")
    print("  1. Standard 8-step CW rotation test")
    print("  2. Full rotation encoder calibration")
    print("  3. Home width calibration")
    try:
        choice = raw_input("Enter choice (1/2/3): ").strip()
    except NameError:
        choice = input("Enter choice (1/2/3): ").strip()

    if choice == "2":
        full_rotation_test(dome)
        with open(state_file, "w") as f:
            json.dump({"position": dome.get_pos()}, f)
        return
    elif choice == "3":
        calibrate_home_width(dome)
        with open(state_file, "w") as f:
            json.dump({"position": dome.get_pos()}, f)
        return
    else:
        standard_rotation_test(dome, state_file)


if __name__ == "__main__":
    main()
