#!/usr/bin/env python
"""
Real hardware test for dome rotation and telemetry.
Rotates dome for 30 seconds, prints telemetry to console at each polling interval.
"""
import time

from dome import Dome

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
    dome.set_rotation(dome.CW)
    dome.start_rotation()
    start_time = time.time()
    poll_interval = dome.POLL if hasattr(dome, "POLL") else 0.2
    homes = 0
    CW_TEST_DURATION = 150  # seconds
    CCW_TEST_DURATION = 120  # seconds
    stop_at_home = True
    cwtime = 0
    ccwtime = 0
    try:
        while time.time() - start_time < CW_TEST_DURATION:
            position = dome.get_pos()
            # counters = dome.counter_read()
            counters = (dome.dome.digital_in(dome.A), dome.dome.digital_in(dome.B))
            home_switch = dome.dome.digital_in(dome.HOME)
            digital_mask = (
                dome.dome.read_all_digital()
                if hasattr(dome.dome, "read_all_digital")
                else None
            )

            print("Telemetry:")
            print("  Position: {}".format(position))
            print("  Encoders: {}".format(counters))
            print("  Gray code: {}".format(dome.read_encoder_state()))
            print(
                "  Rotation Direction: {}".format(
                    dome.detect_encoder_direction(dome.read_encoder_state())
                )
            )
            print("  Home Switch: {}".format(home_switch))
            print("  Homes: {}".format(homes))
            print(
                "  Digital input bitmask: {}".format(
                    bin(digital_mask)[2:].zfill(5)
                    if digital_mask is not None
                    else "N/A"
                )
            )
            print("  is_turning: {}".format(dome.is_turning))
            print("  Direction: {}".format("CW" if dome.dir == dome.CW else "CCW"))
            print("---")
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
    finally:
        dome.stop_rotation()
        cwtime = time.time() - start_time
        print("Test complete. Dome stopped. total homes: {}".format(homes))
        print("---Time to rotate back to home: {}".format(cwtime))

    cwhomes = homes

    dome.set_rotation(dome.CCW)
    dome.start_rotation()
    start_time = time.time()
    homes = 0
    try:
        while time.time() - start_time < CCW_TEST_DURATION:
            position = dome.get_pos()
            # counters = dome.counter_read()
            counters = (dome.dome.digital_in(dome.A), dome.dome.digital_in(dome.B))
            home_switch = dome.dome.digital_in(dome.HOME)
            digital_mask = (
                dome.dome.read_all_digital()
                if hasattr(dome.dome, "read_all_digital")
                else None
            )

            print("Telemetry:")
            print("  Position: {}".format(position))
            print("  Encoders: {}".format(counters))
            print("  Gray code: {}".format(dome.read_encoder_state()))
            print(
                "  Rotation Direction: {}".format(
                    dome.detect_encoder_direction(dome.read_encoder_state())
                )
            )
            print("  Home Switch: {}".format(home_switch))
            print("  Homes: {}".format(homes))
            print(
                "  Digital input bitmask: {}".format(
                    bin(digital_mask)[2:].zfill(5)
                    if digital_mask is not None
                    else "N/A"
                )
            )
            print("  is_turning: {}".format(dome.is_turning))
            print("  Direction: {}".format("CW" if dome.dir == dome.CW else "CCW"))
            print("---")
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
    finally:
        dome.stop_rotation()
        ccwtime = time.time() - start_time
        print("Test complete. Dome stopped. total homes: {}".format(homes))
        print("---Time to rotate back to home: {}".format(ccwtime))

    print("Total home switch activations during CW rotation: {}".format(cwhomes))
    print("Total home switch activations during CCW rotation: {}".format(homes))
    print("---Time to rotate back to home(CW): {}".format(cwtime))
    print("---Time to rotate back to home(CCW): {}".format(ccwtime))
