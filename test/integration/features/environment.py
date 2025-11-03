"""
Behave configuration for dome control BDD tests.

This file configures the test environment and provides setup/teardown hooks.
Placed under test/integration/features so Behave auto-discovers it.
"""

import os
import sys
import time

# Ensure project root and indi_driver/lib are importable
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIB_DIR = os.path.join(ROOT_DIR, "indi_driver", "lib")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if LIB_DIR not in sys.path:
    sys.path.insert(0, LIB_DIR)


def before_all(context):
    """Setup before all tests."""
    print("\n" + "=" * 80)
    print("🔭 DOME CONTROL SYSTEM - BDD TEST SUITE")
    print("=" * 80)

    # Determine test mode from environment or default to smoke test
    test_mode = os.environ.get("DOME_TEST_MODE", "smoke").lower()
    context.test_mode = test_mode

    # Initialize application config separately from Behave's own context.config
    # DO NOT overwrite context.config (reserved by Behave)
    context.app_config = None

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

    # Load application config (this should always succeed with defaults)
    context.app_config = load_config()

    # Set smoke test mode based on test_mode - flatten for compatibility with step files
    if hasattr(context, "test_mode") and context.test_mode == "smoke":
        context.app_config["smoke_test"] = True
        if "testing" in context.app_config:
            context.app_config["testing"]["smoke_test"] = True
    else:
        context.app_config["smoke_test"] = False
        if "testing" in context.app_config:
            context.app_config["testing"]["smoke_test"] = False


def before_scenario(context, scenario):
    """Setup before each scenario."""
    print(f"\n🧪 SCENARIO: {scenario.name}")

    # Import dome modules
    try:
        from dome import Dome

        # Create dome instance with application config (avoid Behave's context.config)
        context.dome = Dome(getattr(context, "app_config", {}))

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
    """Cleanup after each scenario.

    Keep this hook extremely defensive to avoid any exceptions propagating
    to Behave that could cause a cleanup_error result. We intentionally
    minimize logic and swallow any unexpected errors.
    """
    try:
        # Only perform essential hardware safety in hardware mode.
        if (
            hasattr(context, "dome")
            and getattr(context, "test_mode", "smoke") == "hardware"
        ):
            try:
                if hasattr(context.dome, "emergency_stop"):
                    context.dome.emergency_stop()
            except Exception:
                # Never propagate cleanup issues
                pass

        # Soft tracking for summaries (non-critical)
        try:
            if str(getattr(scenario, "status", "")).lower().endswith("passed"):
                context.scenarios_passed = getattr(context, "scenarios_passed", 0) + 1
            else:
                context.scenarios_failed = getattr(context, "scenarios_failed", 0) + 1
        except Exception:
            pass
    except Exception:
        # Absolutely never raise from cleanup
        pass


def after_feature(context, feature):
    """Cleanup after each feature.

    Avoid any operations that could raise and lead to Behave reporting
    cleanup_error. Summaries are optional; we prefer stability here.
    """
    try:
        # Optionally compute but do not print (printing can fail on CI encodings)
        _ = getattr(context, "scenarios_passed", 0) + getattr(
            context, "scenarios_failed", 0
        )
        # No-op by design
        return None
    except Exception:
        # Swallow absolutely everything in cleanup
        return None


def after_all(context):
    """Cleanup after all tests.

    Keep as a no-op to prevent any potential cleanup_error classifications.
    """
    try:
        # No global cleanup necessary in smoke mode; hardware mode guarded elsewhere
        return None
    except Exception:
        return None


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
