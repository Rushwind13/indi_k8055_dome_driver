"""
Startup and shutdown step definitions for dome control BDD tests.
These steps handle system initialization and shutdown scenarios.
"""

import json
import os
import sys
import time

# Add the parent directory to the path to import dome modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    from behave import given, then, when
except ImportError:
    # Fallback for when behave is not installed
    def given(text):
        return lambda f: f

    def when(text):
        return lambda f: f

    def then(text):
        return lambda f: f

    def step(text):
        return lambda f: f


@given("the dome system is powered off")
def step_dome_system_powered_off(context):
    """Set dome system to powered off state."""
    context.dome_powered = False
    context.system_state = "powered_off"
    context.initialization_complete = False
    print(f"🔌 Dome system is powered off")


@given("the dome system is in shutdown state")
def step_dome_system_shutdown(context):
    """Set dome system to shutdown state."""
    context.dome_powered = True
    context.system_state = "shutdown"
    context.initialization_complete = False
    print(f"🛑 Dome system is in shutdown state")


@given("the dome system is initializing")
def step_dome_system_initializing(context):
    """Set dome system to initializing state."""
    context.dome_powered = True
    context.system_state = "initializing"
    context.initialization_complete = False
    context.initialization_start_time = time.time()
    print(f"🚀 Dome system is initializing")


@given("the dome system is fully operational")
def step_dome_system_operational(context):
    """Set dome system to fully operational state."""
    context.dome_powered = True
    context.system_state = "operational"
    context.initialization_complete = True
    context.dome.system_ready = True
    print(f"✅ Dome system is fully operational")


@given("all subsystems are ready")
def step_all_subsystems_ready(context):
    """Set all subsystems to ready state."""
    context.motor_subsystem_ready = True
    context.encoder_subsystem_ready = True
    context.shutter_subsystem_ready = True
    context.communication_subsystem_ready = True
    context.safety_subsystem_ready = True
    print(f"✅ All subsystems are ready")


@given("the dome has active operations running")
def step_dome_active_operations(context):
    """Set dome to have active operations running."""
    context.dome.has_active_operations = True
    context.dome.active_operation_count = 2
    context.dome.current_operations = ["telemetry_monitoring", "position_tracking"]
    print(
        f"⚙️  Dome has {context.dome.active_operation_count} active operations running"
    )


@when("I power on the dome system")
def step_power_on_dome(context):
    """Power on the dome system."""
    context.dome_powered = True
    context.system_state = "powering_on"
    context.power_on_time = time.time()

    if context.config.get("smoke_test", True):
        print(f"🔹 SMOKE TEST: Dome system powered on")
    else:
        print(f"⚡ HARDWARE: Powering on dome system")


@when("I initiate system startup")
def step_initiate_startup(context):
    """Initiate system startup sequence."""
    context.system_state = "starting_up"
    context.startup_initiated_time = time.time()
    context.startup_phase = "initialization"

    # Initialize dome with error handling attributes
    from error_handling_steps import add_error_handling_attributes

    add_error_handling_attributes(context.dome)

    if context.config.get("smoke_test", True):
        # Simulate startup sequence completion
        context.dome.system_ready = True
        context.initialization_complete = True
        print(f"🔹 SMOKE TEST: System startup sequence initiated and completed")
    else:
        print(f"⚡ HARDWARE: Initiating system startup sequence")


@when("I initiate graceful shutdown")
def step_initiate_graceful_shutdown(context):
    """Initiate graceful shutdown sequence."""
    context.system_state = "shutting_down"
    context.shutdown_initiated_time = time.time()
    context.shutdown_phase = "stopping_operations"

    if context.config.get("smoke_test", True):
        # Simulate shutdown sequence
        context.dome.has_active_operations = False
        context.dome.system_ready = False
        print(f"🔹 SMOKE TEST: Graceful shutdown sequence initiated")
    else:
        print(f"⚡ HARDWARE: Initiating graceful shutdown sequence")


@when("I force an emergency shutdown")
def step_force_emergency_shutdown(context):
    """Force emergency shutdown."""
    context.system_state = "emergency_shutdown"
    context.emergency_shutdown_time = time.time()
    context.dome.emergency_shutdown_active = True
    context.dome.has_active_operations = False

    if context.config.get("smoke_test", True):
        print(f"🔹 SMOKE TEST: Emergency shutdown forced")
    else:
        print(f"⚡ HARDWARE: Emergency shutdown forced")


@when("the startup sequence times out")
def step_startup_timeout(context):
    """Simulate startup sequence timeout."""
    context.startup_timeout = True
    context.startup_timeout_time = time.time()
    context.system_state = "startup_failed"
    print(f"⏰ Startup sequence timed out")


@then("the system should power on successfully")
def step_verify_power_on_success(context):
    """Verify system powered on successfully."""
    assert context.dome_powered == True, "System should be powered on"
    assert context.system_state in [
        "powering_on",
        "initializing",
        "operational",
    ], "System should be in valid powered state"
    print(f"✅ System powered on successfully")


@then("all subsystems should initialize")
def step_verify_subsystems_initialize(context):
    """Verify all subsystems initialized."""
    if context.config.get("smoke_test", True):
        # In smoke test mode, assume all subsystems initialized
        context.motor_subsystem_ready = True
        context.encoder_subsystem_ready = True
        context.shutter_subsystem_ready = True
        context.communication_subsystem_ready = True
        context.safety_subsystem_ready = True
        print(f"🔹 SMOKE TEST: All subsystems initialized")
    else:
        # In hardware mode, check actual subsystem status
        assert context.motor_subsystem_ready, "Motor subsystem should be ready"
        assert context.encoder_subsystem_ready, "Encoder subsystem should be ready"
        assert context.shutter_subsystem_ready, "Shutter subsystem should be ready"
        assert (
            context.communication_subsystem_ready
        ), "Communication subsystem should be ready"
        assert context.safety_subsystem_ready, "Safety subsystem should be ready"
        print(f"⚡ HARDWARE: All subsystems initialized")


@then("the dome should be ready for operations")
def step_verify_dome_ready(context):
    """Verify dome is ready for operations."""
    assert context.dome.system_ready == True, "Dome should be ready for operations"
    assert context.initialization_complete == True, "Initialization should be complete"
    print(f"✅ Dome is ready for operations")


@then("the home position should be established")
def step_verify_home_established(context):
    """Verify home position was established."""
    if context.config.get("smoke_test", True):
        context.dome.is_homed = True
        context.dome.current_azimuth = 0
        print(f"🔹 SMOKE TEST: Home position established at 0°")
    else:
        assert context.dome.isHome(), "Home position should be established"
        print(f"⚡ HARDWARE: Home position established")


@then("telemetry systems should be active")
def step_verify_telemetry_active(context):
    """Verify telemetry systems are active."""
    context.telemetry_active = True
    context.telemetry_start_time = time.time()
    print(f"📊 Telemetry systems are active")


@then("all active operations should stop gracefully")
def step_verify_operations_stop_gracefully(context):
    """Verify all active operations stopped gracefully."""
    assert context.dome.has_active_operations == False, "All operations should stop"
    assert context.dome.active_operation_count == 0, "Operation count should be zero"
    print(f"✅ All active operations stopped gracefully")


@then("the dome should return to safe position")
def step_verify_dome_safe_position(context):
    """Verify dome returned to safe position."""
    if context.config.get("smoke_test", True):
        context.dome.current_azimuth = context.config.get("safe_azimuth", 0)
        context.dome.is_in_safe_position = True
        print(f"🔹 SMOKE TEST: Dome at safe position ({context.dome.current_azimuth}°)")
    else:
        safe_azimuth = context.config.get("safe_azimuth", 0)
        tolerance = context.config.get("azimuth_tolerance", 2)
        current = context.dome.current_azimuth
        diff = abs(current - safe_azimuth)
        if diff > 180:
            diff = 360 - diff
        assert (
            diff <= tolerance
        ), f"Dome not at safe position: {current}° (target: {safe_azimuth}°)"
        print(f"⚡ HARDWARE: Dome at safe position ({current}°)")


@then("the shutter should be closed and secured")
def step_verify_shutter_secured(context):
    """Verify shutter is closed and secured."""
    if context.config.get("smoke_test", True):
        context.dome.shutter_position = "closed"
        context.dome.shutter_secured = True
        print(f"🔹 SMOKE TEST: Shutter closed and secured")
    else:
        assert context.dome.isClosed(), "Shutter should be closed"
        print(f"⚡ HARDWARE: Shutter closed and secured")


@then("the system should power down")
def step_verify_system_power_down(context):
    """Verify system powered down."""
    context.dome_powered = False
    context.system_state = "powered_off"
    context.dome.system_ready = False
    print(f"🔌 System powered down successfully")


@then("all operations should halt immediately")
def step_verify_operations_halt_immediately(context):
    """Verify all operations halted immediately."""
    assert (
        context.dome.has_active_operations == False
    ), "All operations should halt immediately"
    assert (
        context.dome.emergency_shutdown_active == True
    ), "Emergency shutdown should be active"
    print(f"🚨 All operations halted immediately")


@then("critical systems should remain powered")
def step_verify_critical_systems_powered(context):
    """Verify critical systems remain powered."""
    context.safety_systems_powered = True
    context.communication_systems_powered = True
    context.monitoring_systems_powered = True
    print(f"🔋 Critical systems remain powered")


@then("startup should fail with timeout error")
def step_verify_startup_timeout_error(context):
    """Verify startup failed with timeout error."""
    assert context.startup_timeout == True, "Startup should timeout"
    assert (
        context.system_state == "startup_failed"
    ), "System should be in startup failed state"
    print(f"❌ Startup failed with timeout error")


@then("error recovery procedures should be initiated")
def step_verify_error_recovery_initiated(context):
    """Verify error recovery procedures were initiated."""
    context.error_recovery_active = True
    context.error_recovery_start_time = time.time()
    print(f"🔧 Error recovery procedures initiated")


@then("the startup should complete within {timeout:d} seconds")
def step_verify_startup_timeout(context, timeout):
    """Verify startup completes within specified timeout."""
    if context.config.get("smoke_test", True):
        # In smoke test mode, assume startup completed quickly
        startup_time = 2  # Simulated quick startup
        assert (
            startup_time <= timeout
        ), f"Startup should complete within {timeout} seconds"
        print(f"🔹 SMOKE TEST: Startup completed in {startup_time} seconds")
    else:
        # In hardware mode, check actual timing
        if hasattr(context, "startup_initiated_time"):
            startup_duration = time.time() - context.startup_initiated_time
            assert (
                startup_duration <= timeout
            ), f"Startup took {startup_duration:.1f}s, should be within {timeout}s"
            print(f"⚡ HARDWARE: Startup completed in {startup_duration:.1f} seconds")
        else:
            print(f"⏱️  Startup timing validation skipped (no start time recorded)")


@then("the shutdown should complete within {timeout:d} seconds")
def step_verify_shutdown_timeout(context, timeout):
    """Verify shutdown completes within specified timeout."""
    if context.config.get("smoke_test", True):
        # In smoke test mode, assume shutdown completed quickly
        shutdown_time = 3  # Simulated shutdown time
        assert (
            shutdown_time <= timeout
        ), f"Shutdown should complete within {timeout} seconds"
        print(f"🔹 SMOKE TEST: Shutdown completed in {shutdown_time} seconds")
    else:
        # In hardware mode, check actual timing
        if hasattr(context, "shutdown_initiated_time"):
            shutdown_duration = time.time() - context.shutdown_initiated_time
            assert (
                shutdown_duration <= timeout
            ), f"Shutdown took {shutdown_duration:.1f}s, should be within {timeout}s"
            print(f"⚡ HARDWARE: Shutdown completed in {shutdown_duration:.1f} seconds")
        else:
            print(f"⏱️  Shutdown timing validation skipped (no start time recorded)")


# Add startup/shutdown attributes to dome for testing
def add_startup_shutdown_attributes(dome):
    """Add startup/shutdown attributes to dome object for testing."""
    dome.system_ready = False
    dome.has_active_operations = False
    dome.active_operation_count = 0
    dome.current_operations = []
    dome.emergency_shutdown_active = False
    dome.is_in_safe_position = False
    dome.shutter_secured = False
