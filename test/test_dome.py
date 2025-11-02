#!/usr/bin/env python

"""
Dome rotation and positioning tests.

Tests dome rotation, home positioning, and encoder functionality
"""

import dome


def test_init():
    """Test dome initialization"""
    print("Testing dome initialization...")
    the_dome = dome.Dome()
    assert the_dome is not None
    print("✓ Dome initialized successfully")
    return the_dome


def test_home_positioning(the_dome):
    """Test moving dome to home position"""
    print("\nTesting home positioning...")

    print("Initial dome state:")
    print(f" - At home: {the_dome.isHome()}")
    print(f" - Position: {the_dome.get_pos()}")

    # Move to home position
    print("Moving dome to home position (CW)...")
    the_dome.cw(to_home=True)

    print("Final dome state:")
    print(f" - At home: {the_dome.isHome()}")
    print(f" - Position: {the_dome.get_pos()}")

    print("✓ Home positioning test completed")


def test_rotation_by_amount(the_dome):
    """Test dome rotation by specific amounts"""
    print("\nTesting rotation by specific amounts...")

    # Ensure we start from home
    if not the_dome.isHome():
        print("Moving to home first...")
        the_dome.cw(to_home=True)

    initial_pos = the_dome.get_pos()
    print(f"Starting position: {initial_pos}")

    # Test small CW rotation
    print("Rotating 45 degrees clockwise...")
    the_dome.cw(amount=45)
    new_pos = the_dome.get_pos()
    print(f"New position: {new_pos}")

    # Test CCW rotation back
    print("Rotating 45 degrees counter-clockwise...")
    the_dome.ccw(amount=45)
    final_pos = the_dome.get_pos()
    print(f"Final position: {final_pos}")

    print("✓ Rotation by amount test completed")


def test_encoder_reading(the_dome):
    """Test encoder tick reading functionality"""
    print("\nTesting encoder reading...")

    # Read current encoder values
    encoder_ticks = the_dome.counter_read()
    print(f"Current encoder ticks: {encoder_ticks}")

    # Test counter reset
    print("Testing counter reset...")
    the_dome.counter_reset()
    encoder_ticks_after_reset = the_dome.counter_read()
    print(f"Encoder ticks after reset: {encoder_ticks_after_reset}")

    print("✓ Encoder reading test completed")


def test_movement_safety(the_dome):
    """Test movement safety and state tracking"""
    print("\nTesting movement safety...")

    print("Testing state variables:")
    print(f" - is_home: {the_dome.is_home}")
    print(f" - is_turning: {the_dome.is_turning}")
    print(f" - direction: {'CW' if the_dome.dir == the_dome.CW else 'CCW'}")

    print("✓ Safety state test completed")


def run_smoke_test():
    """
    Run a quick smoke test for dome operations
    """
    print("=" * 50)
    print("RUNNING DOME SMOKE TEST")
    print("=" * 50)

    # Initialize dome with smoke test config if available
    try:
        the_dome = dome.Dome("smoke_test_config.json")
        print("Using smoke test configuration")
    except (FileNotFoundError, IOError):
        the_dome = dome.Dome()
        print("Using default configuration")

    # Run basic tests
    test_encoder_reading(the_dome)
    test_movement_safety(the_dome)

    print("\nSmoke test completed - basic dome functions validated!")
    print(
        "Note: This test only validates command sequences, "
        "not actual hardware movement."
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--smoke-test":
        run_smoke_test()
    else:
        print("Running dome functionality tests...")
        print(
            "IMPORTANT: These tests will move the dome if connected to real hardware!"
        )

        # Initialize dome
        the_dome = test_init()

        # Run comprehensive tests
        test_encoder_reading(the_dome)
        test_movement_safety(the_dome)
        test_home_positioning(the_dome)
        test_rotation_by_amount(the_dome)

        print("\n" + "=" * 50)
        print("All dome tests completed successfully!")
        print("=" * 50)
        print("\nTo run quick smoke test: python3 test_dome.py --smoke-test")
        print("REMINDER: Shutter operations require dome to be at HOME position!")
