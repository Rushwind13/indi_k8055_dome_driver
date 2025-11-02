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

from behave import given, step
from config import load_config

from dome import Dome


@given("the dome controller is initialized")
def step_dome_controller_initialized(context):
    """Initialize the dome controller for testing."""
    # Load a deterministic config for tests and force mock/smoke settings
    config = load_config()
    config.setdefault("testing", {})
    config["testing"]["smoke_test"] = True
    # Provide a short smoke timeout to make shutter timing deterministic in tests
    config["testing"].setdefault("smoke_test_timeout", 0.1)
    context.config = config
    context.dome = Dome(config)


@step("I wait {seconds:d} seconds")
def step_wait_seconds(context, seconds):
    """Non-blocking wait for smoke tests; blocking in hardware mode."""
    if context.config.get("testing", {}).get("smoke_test", True):
        # don't actually sleep in smoke tests
        print(f"🔹 SMOKE TEST: Simulated wait of {seconds} seconds")
    else:
        time.sleep(seconds)


@given("telemetry monitoring is active")
def step_telemetry_monitoring_active(context):
    context.telemetry_active = True
    context.telemetry_data = {}
