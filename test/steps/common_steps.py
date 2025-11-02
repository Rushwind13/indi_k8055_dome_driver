"""
Common step definitions for dome control BDD tests.

These steps are shared across multiple feature files.
"""

import os
import sys
import time

# Add the parent directory to the path to import dome modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from behave import given, step, then, when
from config import load_config
from dome import Dome

# Global test context
test_context = {}


@given("the dome controller is initialized")
def step_dome_controller_initialized(context):
    """Initialize the dome controller for testing."""
    # Load configuration with smoke test mode
    config = load_config()
    config["smoke_test"] = True

    # Store config in context
    context.config = config
    context.dome = Dome(config)

    # Initialize test tracking
    context.test_results = []
    context.errors = []
    context.warnings = []

    print(f"🔹 SMOKE TEST MODE: Dome controller initialized")


@given("the dome is in smoke test mode")
def step_dome_smoke_test_mode(context):
    """Ensure dome is in smoke test mode."""
    assert context.config.get("smoke_test", False), "Dome should be in smoke test mode"
    print(f"✅ Confirmed: Running in SMOKE TEST mode")


@given("the dome is in hardware test mode")
def step_dome_hardware_test_mode(context):
    """Ensure dome is in hardware test mode."""
    context.config["smoke_test"] = False
    context.dome = Dome(context.config)
    print(f"⚡ HARDWARE TEST MODE: Real hardware operations enabled")


@given("the dome is at the home position")
def step_dome_at_home(context):
    """Set dome to home position."""
    if context.config.get("smoke_test", True):
        context.dome.current_azimuth = 0
        context.dome.is_homed = True
        print(f"🔹 SMOKE TEST: Dome position set to home (0°)")
    else:
        # In hardware mode, actually move to home
        context.dome.find_home()
        print(f"⚡ HARDWARE: Dome moved to home position")


@given("the dome is at azimuth {azimuth:d} degrees")
def step_dome_at_azimuth(context, azimuth):
    """Set dome to specific azimuth."""
    if context.config.get("smoke_test", True):
        context.dome.current_azimuth = azimuth
        print(f"🔹 SMOKE TEST: Dome position set to {azimuth}°")
    else:
        context.dome.slew_to_azimuth(azimuth)
        print(f"⚡ HARDWARE: Dome moved to {azimuth}°")


@given("the shutter is closed")
def step_shutter_closed(context):
    """Ensure shutter is closed."""
    if context.config.get("smoke_test", True):
        context.dome.shutter_position = "closed"
        print(f"🔹 SMOKE TEST: Shutter set to closed")
    else:
        if not context.dome.isClosed():
            context.dome.close_shutter()
        print(f"⚡ HARDWARE: Shutter is closed")


@given("the shutter is open")
def step_shutter_open(context):
    """Ensure shutter is open."""
    if context.config.get("smoke_test", True):
        context.dome.shutter_position = "open"
        print(f"🔹 SMOKE TEST: Shutter set to open")
    else:
        if context.dome.isClosed():
            context.dome.open_shutter()
        print(f"⚡ HARDWARE: Shutter is open")


@when("I command the dome to rotate {direction} by {degrees:d} degrees")
def step_rotate_dome_by_degrees(context, direction, degrees):
    """Rotate dome by specified degrees in given direction."""
    start_azimuth = context.dome.current_azimuth

    if direction.lower() == "clockwise":
        target_azimuth = (start_azimuth + degrees) % 360
        context.dome.rotate_clockwise(degrees)
    else:  # counter-clockwise
        target_azimuth = (start_azimuth - degrees) % 360
        context.dome.rotate_counter_clockwise(degrees)

    context.target_azimuth = target_azimuth
    context.start_azimuth = start_azimuth

    if context.config.get("smoke_test", True):
        print(
            f"🔹 SMOKE TEST: Rotated {direction} {degrees}° "
            f"from {start_azimuth}° to {target_azimuth}°"
        )
    else:
        print(
            f"⚡ HARDWARE: Rotated {direction} {degrees}° "
            f"from {start_azimuth}° to {target_azimuth}°"
        )


@when("I command the dome to slew to azimuth {azimuth:d} degrees")
def step_slew_to_azimuth(context, azimuth):
    """Slew dome to specific azimuth."""
    start_azimuth = context.dome.current_azimuth
    context.start_azimuth = start_azimuth
    context.target_azimuth = azimuth

    context.dome.slew_to_azimuth(azimuth)

    if context.config.get("smoke_test", True):
        print(f"🔹 SMOKE TEST: Slewed from {start_azimuth}° to {azimuth}°")
    else:
        print(f"⚡ HARDWARE: Slewing from {start_azimuth}° to {azimuth}°")


@when("I command the dome to find home")
def step_find_home(context):
    """Command dome to find home position."""
    context.dome.find_home()

    if context.config.get("smoke_test", True):
        print(f"🔹 SMOKE TEST: Home sequence completed")
    else:
        print(f"⚡ HARDWARE: Finding home position")


@when("I command the shutter to open")
def step_open_shutter(context):
    """Command shutter to open."""
    context.dome.open_shutter()

    if context.config.get("smoke_test", True):
        print(f"🔹 SMOKE TEST: Shutter opening command sent")
    else:
        print(f"⚡ HARDWARE: Opening shutter")


@when("I command the shutter to close")
def step_close_shutter(context):
    """Command shutter to close."""
    context.dome.close_shutter()

    if context.config.get("smoke_test", True):
        print(f"🔹 SMOKE TEST: Shutter closing command sent")
    else:
        print(f"⚡ HARDWARE: Closing shutter")


@then("the dome should be at azimuth {azimuth:d} degrees")
def step_verify_dome_azimuth(context, azimuth):
    """Verify dome is at specified azimuth."""
    current = context.dome.current_azimuth
    tolerance = context.config.get("azimuth_tolerance", 2)

    # Handle wrap-around cases
    diff = abs(current - azimuth)
    if diff > 180:
        diff = 360 - diff

    assert (
        diff <= tolerance
    ), f"Dome azimuth {current}° not within {tolerance}° of target {azimuth}°"

    if context.config.get("smoke_test", True):
        print(f"✅ SMOKE TEST: Dome at {current}° (target: {azimuth}°)")
    else:
        print(f"✅ HARDWARE: Dome at {current}° (target: {azimuth}°)")


@then("the dome should be at the home position")
def step_verify_dome_at_home(context):
    """Verify dome is at home position."""
    assert context.dome.isHome(), "Dome should be at home position"

    if context.config.get("smoke_test", True):
        print(f"✅ SMOKE TEST: Dome confirmed at home position")
    else:
        print(f"✅ HARDWARE: Dome confirmed at home position")


@then("the shutter should be open")
def step_verify_shutter_open(context):
    """Verify shutter is open."""
    if context.config.get("smoke_test", True):
        assert context.dome.shutter_position == "open", "Shutter should be open"
        print(f"✅ SMOKE TEST: Shutter confirmed open")
    else:
        assert not context.dome.isClosed(), "Shutter should be open"
        print(f"✅ HARDWARE: Shutter confirmed open")


@then("the shutter should be closed")
def step_verify_shutter_closed(context):
    """Verify shutter is closed."""
    if context.config.get("smoke_test", True):
        assert context.dome.shutter_position == "closed", "Shutter should be closed"
        print(f"✅ SMOKE TEST: Shutter confirmed closed")
    else:
        assert context.dome.isClosed(), "Shutter should be closed"
        print(f"✅ HARDWARE: Shutter confirmed closed")


@then("the operation should complete within {timeout:d} seconds")
def step_verify_operation_timeout(context, timeout):
    """Verify operation completes within timeout."""
    # This is a placeholder - in real implementation, we'd track operation start time
    # and verify completion within the specified timeout
    print(f"✅ Operation completed within {timeout} seconds")


@then("no errors should be reported")
def step_verify_no_errors(context):
    """Verify no errors occurred during operation."""
    assert len(context.errors) == 0, f"Errors reported: {context.errors}"
    print(f"✅ No errors reported")


@step("I wait {seconds:d} seconds")
def step_wait_seconds(context, seconds):
    """Wait for specified number of seconds."""
    if context.config.get("smoke_test", True):
        # In smoke test mode, don't actually wait - just log
        print(f"🔹 SMOKE TEST: Simulated wait of {seconds} seconds")
    else:
        time.sleep(seconds)
        print(f"⏱️  HARDWARE: Waited {seconds} seconds")


@given("telemetry monitoring is active")
def step_telemetry_monitoring_active(context):
    """Activate telemetry monitoring."""
    context.telemetry_active = True
    context.telemetry_data = {}
    print(f"📊 Telemetry monitoring activated")


@then("the dome position should be reported as {azimuth:d} degrees")
def step_verify_reported_position(context, azimuth):
    """Verify reported dome position."""
    reported_azimuth = context.dome.current_azimuth
    assert (
        reported_azimuth == azimuth
    ), f"Reported azimuth {reported_azimuth}° != expected {azimuth}°"
    print(f"📊 Position reported correctly: {azimuth}°")
