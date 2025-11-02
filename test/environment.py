"""
Behave configuration for dome control BDD tests.

This file configures the test environment and provides setup/teardown hooks.
"""

import os
import sys
import time

# Add the parent directory to the path to import dome modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def before_all(context):
    """Setup before all tests."""
    print("\n" + "=" * 80)
    print("🔭 DOME CONTROL SYSTEM - BDD TEST SUITE")
    print("=" * 80)

    # Determine test mode from environment or default to smoke test
    test_mode = os.environ.get("DOME_TEST_MODE", "smoke").lower()
    context.test_mode = test_mode

    # Initialize config attribute at the top level so it can be set in before_feature
    context.config = None

    if test_mode == "smoke":
        print("🔹 RUNNING IN SMOKE TEST MODE")
        print("   - No real hardware operations")
        print("   - Fast execution with simulated responses")
        print("   - Safe for development and CI/CD")
    elif test_mode == "hardware":
        print("⚡ RUNNING IN HARDWARE TEST MODE")
        print("   - REAL HARDWARE OPERATIONS")
        print("   - Physical dome movements")
        print("   - CAUTION: Only run with proper setup")
    else:
        print(f"❌ UNKNOWN TEST MODE: {test_mode}")
        print("   Valid modes: 'smoke' or 'hardware'")
        sys.exit(1)

    print("=" * 80 + "\n")


def before_feature(context, feature):
    """Setup before each feature."""
    print(f"\n📋 FEATURE: {feature.name}")
    print("-" * 60)

    # Initialize test tracking first (before any potential errors)
    context.feature_start_time = time.time()
    context.scenarios_passed = 0
    context.scenarios_failed = 0

    # Load configuration based on test mode
    from config import load_config

    # Load config (this should always succeed with defaults)
    context.config = load_config()

    # Set smoke test mode based on test_mode - flatten for compatibility with step files
    if hasattr(context, "test_mode") and context.test_mode == "smoke":
        context.config["smoke_test"] = True
        if "testing" in context.config:
            context.config["testing"]["smoke_test"] = True
    else:
        context.config["smoke_test"] = False
        if "testing" in context.config:
            context.config["testing"]["smoke_test"] = False


def before_scenario(context, scenario):
    """Setup before each scenario."""
    print(f"\n🧪 SCENARIO: {scenario.name}")

    # Import dome modules
    try:
        from config import load_config

        from dome import Dome

        # Create dome instance
        context.dome = Dome(context.config)

        # Add test-specific attributes
        add_test_attributes(context.dome)

        # Initialize scenario tracking
        context.scenario_start_time = time.time()
        context.test_results = []
        context.errors = []
        context.warnings = []

    except Exception as e:
        print(f"❌ Error setting up scenario: {e}")
        context.setup_error = str(e)


def after_scenario(context, scenario):
    """Cleanup after each scenario."""
    try:
        # Be defensive: some setup failures may not set scenario_start_time
        scenario_start = getattr(context, "scenario_start_time", None)
        if scenario_start is None:
            scenario_duration = 0.0
        else:
            scenario_duration = time.time() - scenario_start

        if scenario.status == "passed":
            context.scenarios_passed = getattr(context, "scenarios_passed", 0) + 1
            status_icon = "✅"
            status_text = "PASSED"
        else:
            context.scenarios_failed = getattr(context, "scenarios_failed", 0) + 1
            status_icon = "❌"
            status_text = "FAILED"

        print(f"{status_icon} {status_text} in {scenario_duration:.2f}s")

        # Cleanup dome state if needed (only for hardware mode)
        if (
            hasattr(context, "dome")
            and getattr(context, "test_mode", "smoke") == "hardware"
        ):
            try:
                # In hardware mode, ensure safe state
                if hasattr(context.dome, "emergency_stop"):
                    context.dome.emergency_stop()
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")
    except Exception as e:
        # Ensure cleanup errors do not crash the reporter; report and continue
        print(f"⚠️  after_scenario encountered an exception: {e}")


def after_feature(context, feature):
    """Cleanup after each feature."""
    try:
        # Safely handle case where feature_start_time might not be set
        if hasattr(context, "feature_start_time"):
            feature_duration = time.time() - context.feature_start_time
        else:
            feature_duration = 0.0

        # Safely get scenario counts
        scenarios_passed = getattr(context, "scenarios_passed", 0)
        scenarios_failed = getattr(context, "scenarios_failed", 0)
        total_scenarios = scenarios_passed + scenarios_failed

        print("-" * 60)
        print("📊 FEATURE SUMMARY:")
        print(f"   Total scenarios: {total_scenarios}")
        print(f"   Passed: {scenarios_passed}")
        print(f"   Failed: {scenarios_failed}")
        print(f"   Duration: {feature_duration:.2f}s")
        print("-" * 60)
    except Exception as e:
        # Ensure hook errors are visible and do not crash behave silently
        import traceback

        print(f"⚠️  after_feature raised an exception: {e}")
        traceback.print_exc()


def after_all(context):
    """Cleanup after all tests."""
    try:
        print("\n" + "=" * 80)
        print("🏁 TEST SUITE COMPLETED")

        if getattr(context, "test_mode", "smoke") == "smoke":
            print("🔹 Smoke test mode - No hardware affected")
        else:
            print("⚡ Hardware test mode - Check dome status")

        print("=" * 80)
    except Exception as e:
        import traceback

        print(f"⚠️  after_all raised an exception: {e}")
        traceback.print_exc()


def add_test_attributes(dome):
    """Add test-specific attributes to dome instance."""
    # Import attribute additions from step modules
    try:
        from steps.error_handling_steps import add_error_handling_attributes
        from steps.startup_shutdown_steps import add_startup_shutdown_attributes

        add_error_handling_attributes(dome)
        add_startup_shutdown_attributes(dome)

        # Add additional test attributes
        dome.test_mode_active = True
        dome.test_start_time = time.time()

        # Mock shutter position for smoke tests
        if not hasattr(dome, "shutter_position"):
            dome.shutter_position = "closed"

        # Mock azimuth if not set
        if not hasattr(dome, "current_azimuth"):
            dome.current_azimuth = 0

        # Mock home status
        if not hasattr(dome, "is_homed"):
            dome.is_homed = False

    except ImportError as e:
        print(f"⚠️  Warning: Could not import step modules: {e}")
