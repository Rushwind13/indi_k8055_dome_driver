#!/usr/bin/env python
"""
Real hardware test for dome rotation and telemetry.
Rotates dome for 30 seconds, prints telemetry to console at each polling interval.
"""
import time

from dome import Dome


def Telemetry(context):
    Telemetry_short(context)
    # Telemetry_long(context)  # Uncomment for more detailed telemetry


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
    poll_interval = dome.POLL if hasattr(dome, "POLL") else 0.2
    dome.homes_reset()

    run_time = 0
    telemetry_delay = 0
    homes = 0
    total_ticks = 0

    try:
        while True:
            position = dome.current_pos()
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


if __name__ == "__main__":
    dome = Dome()
    # Use built-in status and counter methods for connection check and telemetry
    try:
        print("Checking dome connection...")
        # Try reading position and counters

        pos = dome.get_pos()
        home_switch = dome.dome.digital_in(dome.HOME)
        print("Connection to dome hardware OK.")
    except Exception as e:
        print("ERROR: Dome hardware not connected: %s" % str(e))
        exit(1)

    print("Starting real hardware test...")

    # Configuration
    FULL_ROTATION_TICKS = 314  # Total ticks for full 360-degree rotation
    DEGREES_PER_STEP = 45  # Rotate 45 degrees each step
    TICKS_PER_STEP = [39, 39, 39, 40] * 2  # Ticks for each 45-degree rotation
    NUM_STEPS = len(TICKS_PER_STEP)  # Number of rotation steps (8 x 45 = 360 deg)

    MAX_SAFETY_TIMEOUT = 300  # Maximum 5 minutes per test (safety)
    stop_at_home = False  # Don't stop at home during individual steps
    min_homes_before_stop = 5

    print("Configuration:")
    print("  Full rotation: {} ticks".format(FULL_ROTATION_TICKS))
    print("  Steps: {} x {} degrees".format(NUM_STEPS, DEGREES_PER_STEP))
    print("  Ticks per step: {}".format(TICKS_PER_STEP))
    print("")

    # Test CW rotation - 8 steps of 45 degrees each
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
                step + 1, dome.current_pos()
            )
        )

    # # Test CCW rotation (encoder tick-based)
    # ccwtime, ccwhomes, ccwticks = test_rotation(
    #     dome=dome,
    #     direction_name="CCW",
    #     rotation_func=dome.ccw,
    #     rotation_amount=CCW_ROTATION_TICKS,
    #     max_duration=MAX_SAFETY_TIMEOUT,
    #     stop_at_home=stop_at_home,
    #     min_homes=1,  # Stop at first home for CCW
    #     use_ticks=True
    # )

    # Print summary
    print("\n" + "=" * 50)
    print("ROTATION TEST SUMMARY")
    print("=" * 50)
    print("CW Rotation ({} steps x {} degrees):".format(NUM_STEPS, DEGREES_PER_STEP))
    print("  Home switches: {}".format(total_cwhomes))
    print("  Encoder ticks: {}".format(total_cwticks))
    print("  Time: {:.2f} seconds".format(total_cwtime))
    print("  Final position: {:.1f} degrees".format(dome.current_pos()))
    print("")
    # print("CCW Rotation:")
    # print("  Home switches: {}".format(ccwhomes))
    # print("  Encoder ticks: {}".format(ccwticks))
    # print("  Time: {:.2f} seconds".format(ccwtime))
    print("=" * 50)
