"""Truly common BDD steps.

Keep this file minimal: initialization, simple helpers like waits, and
telemetry placeholders that are used across feature suites. Domain- and
hardware-specific steps (shutter, rotation, homing) belong in their own
step modules to avoid ambiguous step registrations.
"""

import os
import sys
import time

# Add repository root so imports work regardless of invocation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from behave import given, step  # noqa: E402
from config import load_config  # noqa: E402
from dome import Dome  # noqa: E402


@given("the dome controller is initialized")
def step_dome_controller_initialized(context):
    """Initialize the dome controller for testing."""
    # Load a deterministic config for tests and force mock/smoke settings
    config = load_config()
    config.setdefault("testing", {})
    config["testing"]["smoke_test"] = True
    # Provide a short smoke timeout to make shutter timing deterministic in tests
    config["testing"].setdefault("smoke_test_timeout", 0.1)
    context.app_config = config
    context.dome = Dome(config)
    # Provide a small set of test-only attributes expected by step defs.
    # Keep changes local to tests and non-invasive to production code.
    try:
        # current_azimuth is used by some telemetry steps; prefer get_pos if present
        if not hasattr(context.dome, "current_azimuth"):
            try:
                context.dome.current_azimuth = context.dome.get_pos()
            except Exception:
                context.dome.current_azimuth = getattr(context.dome, "position", 0.0)

        # encoder last reading (A/B) helper
        if not hasattr(context.dome, "encoder_last_reading"):
            try:
                context.dome.encoder_last_reading = context.dome.counter_read()
            except Exception:
                context.dome.encoder_last_reading = {"A": 0, "B": 0}

        # motor and power defaults used across error/telemetry steps
        context.dome.motor_state = getattr(context.dome, "motor_state", "stopped")
        context.dome.operation_state = getattr(context.dome, "operation_state", "idle")
        context.dome.supply_voltage = getattr(context.dome, "supply_voltage", 12.0)
        # Additional test-only defaults used by many step defs
        context.dome.command_queue = getattr(context.dome, "command_queue", [])
        context.dome.motor_operations_suspended = getattr(
            context.dome, "motor_operations_suspended", False
        )
        context.dome.motor_power_state = getattr(
            context.dome, "motor_power_state", "on"
        )
        context.dome.manual_intervention_required = getattr(
            context.dome, "manual_intervention_required", False
        )
        context.dome.system_state = getattr(context.dome, "system_state", "normal")
        context.dome.manual_reset_required = getattr(
            context.dome, "manual_reset_required", False
        )
        # Ensure manual configuration prompt flag exists for config-corruption tests
        context.dome.manual_config_prompt = getattr(
            context.dome, "manual_config_prompt", False
        )
        # Add a small helper used by tests to decide if operations may resume
        if not hasattr(context.dome, "can_resume_operations"):

            def _can_resume():
                return (
                    getattr(context.dome, "power_state", "normal") == "normal"
                    and not getattr(context.dome, "emergency_stop_active", False)
                    and not getattr(context.dome, "motor_stalled", False)
                )

            context.dome.can_resume_operations = _can_resume
        # Ensure a clean error_log and telemetry_data exist for every test run
        context.error_log = []
        context.telemetry_data = {}
    except Exception:
        # Be defensive in case Dome internals change; tests should still initialize
        context.error_log = []
        context.telemetry_data = {}


@step("I wait {seconds:d} seconds")
def step_wait_seconds(context, seconds):
    """Wait that adapts to test mode - blocking in hardware, instant in smoke."""
    # Get timeout multiplier from context/config
    timeout_multiplier = 1.0
    is_hardware_mode = False

    try:
        if hasattr(context, "app_config") and context.app_config:
            testing_config = context.app_config.get("testing", {})
            timeout_multiplier = testing_config.get("timeout_multiplier", 1.0)
            is_hardware_mode = testing_config.get("hardware_mode", False)
    except Exception:
        pass

    # Apply timeout multiplier for hardware mode
    actual_seconds = int(seconds * timeout_multiplier)

    if is_hardware_mode:
        print(f"⚡ HARDWARE MODE: Waiting {actual_seconds} seconds (was {seconds}s)")
        time.sleep(actual_seconds)
    else:
        # Don't actually sleep in smoke tests
        print(f"🔹 SMOKE TEST: Simulated wait of {actual_seconds} seconds")


def get_operation_timeout(context, operation_type="default"):
    """Get appropriate timeout for operation based on test mode."""
    base_timeouts = {
        "shutter": 5,  # Base shutter operation timeout
        "rotation": 10,  # Base rotation timeout
        "park": 15,  # Base park operation timeout
        "goto": 20,  # Base goto operation timeout
        "default": 3,  # Default operation timeout
    }

    base_timeout = base_timeouts.get(operation_type, base_timeouts["default"])

    try:
        if hasattr(context, "app_config") and context.app_config:
            testing_config = context.app_config.get("testing", {})
            timeout_multiplier = testing_config.get("timeout_multiplier", 1.0)
            is_hardware_mode = testing_config.get("hardware_mode", False)

            if is_hardware_mode:
                # Hardware mode gets much longer timeouts
                return int(base_timeout * timeout_multiplier)
            else:
                # Smoke mode keeps base timeouts
                return base_timeout
    except Exception:
        return base_timeout

    return base_timeout


@given("telemetry monitoring is active")
def step_telemetry_monitoring_active(context):
    context.telemetry_active = True
    context.telemetry_data = {}
