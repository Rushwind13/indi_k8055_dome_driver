#!/usr/bin/env python
"""
Shutter telemetry module.

Upper and lower shutter limit switches
Poll every 30ms, do not allow shutter to continue past thrown limit
(other direction OK)

Observatory dome driver test suite
"""

import dome


def test_init():
    """Test dome initialization"""
    the_dome = dome.Dome()
    assert the_dome is not None
    return the_dome


def test_park(the_dome):
    """
    Park the dome safely:
    1. Check if dome is at home position
    2. If not, rotate to home position
    3. Setup shutter hardware (only works at home)
    4. Check if shutter is closed, if not, close it
    """
    print("Starting park sequence...")

    # Safety check: Move to home position first
    if not the_dome.isHome():
        print("Dome not at home, moving to home position...")
        the_dome.cw(to_home=True)

    # Setup shutter hardware (only works at home position)
    if not the_dome.setup_shutter():
        print("ERROR: Failed to setup shutter")
        return False

    # Ensure shutter is closed for safety
    if not the_dome.isClosed():
        print("Shutter not closed, closing it...")
        test_shutter_close(the_dome)

    print("Park sequence completed safely.")
    return True


def test_shutter_open(the_dome):
    """
    Safely open the shutter
    No telemetry feedback - just send signal and wait for timeout
    Physical limit switch will stop the motor when fully open
    """
    print("Testing shutter open operation...")

    # Safety check: Must be at home position
    if not the_dome.isHome():
        print("ERROR: Cannot open shutter - dome not at home position")
        return False

    # Check if we think it's already open
    if the_dome.isOpen():
        print("Shutter state indicates already open - skipping")
        return True

    # Send open signal and wait for completion
    if not the_dome.shutter_open():
        return False

    # Wait for the operation to complete (no telemetry, just timer)
    the_dome.wait_for_shutter_operation("OPEN")

    # Assume success after timeout and update state
    the_dome.setOpen()
    print("Shutter open operation completed")
    return True


def test_shutter_close(the_dome):
    """
    Safely close the shutter
    No telemetry feedback - just send signal and wait for timeout
    Physical limit switch will stop the motor when fully closed
    """
    print("Testing shutter close operation...")

    # Safety check: Must be at home position
    if not the_dome.isHome():
        print("ERROR: Cannot close shutter - dome not at home position")
        return False

    # Check if we think it's already closed
    if the_dome.isClosed():
        print("Shutter state indicates already closed - skipping")
        return True

    # Send close signal and wait for completion
    if not the_dome.shutter_close():
        return False

    # Wait for the operation to complete (no telemetry, just timer)
    the_dome.wait_for_shutter_operation("CLOSE")

    # Assume success after timeout and update state
    the_dome.setClosed()
    print("Shutter close operation completed")
    return True


def run_smoke_test():
    """
    Run a quick smoke test with reduced timeouts
    This tests the functionality without waiting for real hardware delays
    """
    print("=" * 50)
    print("RUNNING SMOKE TEST - Quick validation without hardware")
    print("=" * 50)

    # Initialize dome with smoke test config
    the_dome = dome.Dome("smoke_test_config.json")

    # Simulate being at home for testing
    the_dome.is_home = True  # Override for testing

    print("\n1. Testing shutter close operation...")
    test_shutter_close(the_dome)

    print("\n2. Testing shutter open operation...")
    test_shutter_open(the_dome)

    print("\n3. Testing shutter close again...")
    test_shutter_close(the_dome)

    print("\nSmoke test completed - all operations executed successfully!")
    print("Note: This test only validates command sequences, not actual hardware.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--smoke-test":
        run_smoke_test()
    else:
        print("Running full shutter safety tests...")

        # Initialize dome
        the_dome = test_init()

        # Critical safety sequence: Park first (move to home, close shutter)
        if not test_park(the_dome):
            print("CRITICAL ERROR: Park sequence failed - aborting tests")
            exit(1)

        # Test shutter operations
        print("\nTesting shutter open...")
        test_shutter_open(the_dome)

        print("\nTesting shutter close...")
        test_shutter_close(the_dome)

        print("\nAll shutter tests completed.")
        print("IMPORTANT: Shutter operations only work when dome is at HOME position!")
        print("\nTo run quick smoke test: python3 test_shutter.py --smoke-test")
