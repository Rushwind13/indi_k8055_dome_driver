#!/usr/bin/env python
"""
Real hardware test for dome rotation and telemetry.
Rotates dome for 30 seconds, prints telemetry to console at each polling interval.
"""
import time

from dome import Dome


def Telemetry_short(context):
    print(
        "  {:06.3f}: Digital input bitmask: {}".format(
            context["run_time"],
            bin(context["digital_mask"])[2:].zfill(5)
            if context["digital_mask"] is not None
            else "N/A",
        )
    )


def Telemetry(context):
    enc_state = context["dome"].read_encoder_state()
    print("Telemetry:")
    print("  Run time: {:06.3f} sec".format(context["run_time"]))
    print("  Position: {}".format(context["position"]))
    print("  Encoders: {}".format(context["counters"]))
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

    print("Starting real hardware test: rotating dome for 30 seconds...")
    dome.cw()
    start_time = time.time()
    poll_interval = dome.POLL if hasattr(dome, "POLL") else 0.2
    dome.homes_reset()
    CW_TEST_DURATION = 150  # seconds
    CCW_TEST_DURATION = 120  # seconds
    stop_at_home = True
    cwtime = 0
    ccwtime = 0
    run_time = 0
    try:
        while run_time < CW_TEST_DURATION:
            position = dome.current_pos()
            encoder_ticks, homes = dome.counter_read()
            encoders = (dome.dome.digital_in(dome.A), dome.dome.digital_in(dome.B))
            home_switch = dome.dome.digital_in(dome.HOME)
            digital_mask = (
                dome.dome.read_all_digital()
                if hasattr(dome.dome, "read_all_digital")
                else None
            )

            Telemetry(
                {
                    "run_time": run_time,
                    "dome": dome,
                    "position": position,
                    "encoder_ticks": encoder_ticks,
                    "encoders": encoders,
                    "home_switch": home_switch,
                    "digital_mask": digital_mask,
                    "homes": homes,
                }
            )
            if home_switch:
                print(
                    "Home switch activated {} times during CCW rotation.".format(homes)
                )
                homes += 1
                dome.is_home = True
                dome.set_pos(dome.HOME_POS)
                if stop_at_home and homes > 5:
                    break
            time.sleep(poll_interval)
            run_time = time.time() - start_time
    finally:
        dome.rotation_stop()
        cwtime = run_time
        print("Test complete. Dome stopped. total homes: {}".format(homes))
        print("---Time to rotate back to home: {}".format(cwtime))

    cwhomes = homes

    dome.ccw()
    start_time = time.time()
    run_time = 0
    dome.homes_reset()
    try:
        while run_time < CCW_TEST_DURATION:
            position = dome.current_pos()
            encoder_ticks, homes = dome.counter_read()
            encoders = (dome.dome.digital_in(dome.A), dome.dome.digital_in(dome.B))
            home_switch = dome.dome.digital_in(dome.HOME)
            digital_mask = (
                dome.dome.read_all_digital()
                if hasattr(dome.dome, "read_all_digital")
                else None
            )

            Telemetry(
                {
                    "run_time": run_time,
                    "dome": dome,
                    "position": position,
                    "encoder_ticks": encoder_ticks,
                    "encoders": encoders,
                    "home_switch": home_switch,
                    "digital_mask": digital_mask,
                    "homes": homes,
                }
            )
            if home_switch:
                print(
                    "Home switch activated {} times during CCW rotation.".format(homes)
                )
                homes += 1
                dome.is_home = True
                dome.set_pos(dome.HOME_POS)
                if stop_at_home:
                    break
            time.sleep(poll_interval)
            run_time = time.time() - start_time
    finally:
        dome.rotation_stop()
        ccwtime = run_time
        print("Test complete. Dome stopped. total homes: {}".format(homes))
        print("---Time to rotate back to home: {}".format(ccwtime))

    print("Total home switch activations during CW rotation: {}".format(cwhomes))
    print("Total home switch activations during CCW rotation: {}".format(homes))
    print("---Time to rotate back to home(CW): {}".format(cwtime))
    print("---Time to rotate back to home(CCW): {}".format(ccwtime))
