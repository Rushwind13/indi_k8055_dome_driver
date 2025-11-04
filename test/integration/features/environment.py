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

    # Validate test mode and configure accordingly
    if test_mode == "smoke":
        print("🔹 RUNNING IN SMOKE TEST MODE")
        print("   - No real hardware operations")
        print("   - Fast execution with simulated responses")
        print("   - Safe for development and CI/CD")
        print("   - Timeouts: 1-3 seconds")
        context.hardware_mode = False
        context.timeout_multiplier = 1.0
    elif test_mode == "hardware":
        print("⚡ RUNNING IN HARDWARE TEST MODE")
        print("   - REAL HARDWARE OPERATIONS")
        print("   - Physical dome movements")
        print("   - CAUTION: Only run with proper setup")
        print("   - Timeouts: 30-120 seconds for movements")
        context.hardware_mode = True
        context.timeout_multiplier = 30.0  # Scale timeouts for hardware

        # Validate hardware configuration is available
        _validate_hardware_configuration(context)
    else:
        print(f"❌ UNKNOWN TEST MODE: {test_mode}")
        print("   Valid modes: 'smoke' or 'hardware'")
        sys.exit(1)

    print("=" * 80 + "\n")


def _validate_hardware_configuration(context):
    """Validate that hardware configuration is properly set up."""
    import os

    print("🔍 Validating hardware configuration...")

    # Check for hardware configuration file
    config_paths = [
        "dome_config.json",
        "examples/dome_config_production.json",
        "indi_driver/dome_config.json",
    ]

    config_found = False
    for config_path in config_paths:
        if os.path.exists(config_path):
            config_found = True
            print(f"   ✅ Found config file: {config_path}")
            break

    if not config_found:
        print("   ⚠️  No hardware config found, tests may use default settings")
        print("   📝 Consider creating dome_config.json for hardware testing")

    # Validate environment setup
    if "PYTHONPATH" not in os.environ:
        print("   ⚠️  PYTHONPATH not set, may affect module imports")

    print("   ✅ Hardware mode validation complete")


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

    # Configure for hardware or smoke test mode
    if hasattr(context, "test_mode"):
        if context.test_mode == "smoke":
            # Force smoke test mode in configuration
            context.app_config["smoke_test"] = True
            if "testing" in context.app_config:
                context.app_config["testing"]["smoke_test"] = True
            if "hardware" in context.app_config:
                context.app_config["hardware"]["mock_mode"] = True

            print("   🔧 Configured for smoke test mode")
        elif context.test_mode == "hardware":
            # Configure for hardware mode
            context.app_config["smoke_test"] = False
            if "testing" in context.app_config:
                context.app_config["testing"]["smoke_test"] = False
            if "hardware" in context.app_config:
                context.app_config["hardware"]["mock_mode"] = False

            print("   ⚡ Configured for hardware mode")
            print("   ⚠️  REAL HARDWARE OPERATIONS ENABLED")

        # Add timeout multiplier to config for step files
        if "testing" not in context.app_config:
            context.app_config["testing"] = {}
        context.app_config["testing"]["timeout_multiplier"] = getattr(
            context, "timeout_multiplier", 1.0
        )
        context.app_config["testing"]["hardware_mode"] = getattr(
            context, "hardware_mode", False
        )


def before_scenario(context, scenario):
    """Setup before each scenario."""
    print(f"\n🧪 SCENARIO: {scenario.name}")

    # Import dome modules
    try:
        from dome import Dome

        # Pre-test safety validation for hardware mode
        if getattr(context, "test_mode", "smoke") == "hardware":
            print("   🔒 Performing hardware safety validation...")
            _perform_safety_validation(context)

        # Create dome instance with application config (avoid Behave's context.config)
        context.dome = Dome(getattr(context, "app_config", {}))

        # Add test-specific attributes
        add_test_attributes(context.dome)

        # Initialize scenario tracking
        context.scenario_start_time = time.time()
        context.test_results = []
        context.errors = []
        context.warnings = []

        # Safety initialization for hardware mode
        if getattr(context, "test_mode", "smoke") == "hardware":
            _initialize_hardware_safety(context)

    except Exception as e:
        print(f"❌ Error setting up scenario: {e}")
        context.setup_error = str(e)


def _perform_safety_validation(context):
    """Perform pre-test safety validation for hardware mode."""
    try:
        # Validate abort script is available and executable
        import os
        import subprocess

        ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        abort_script = os.path.join(ROOT_DIR, "indi_driver", "scripts", "abort.py")

        if not os.path.exists(abort_script):
            raise Exception(f"Critical safety script missing: {abort_script}")

        if not os.access(abort_script, os.X_OK):
            raise Exception(f"Abort script not executable: {abort_script}")

        # Test abort script functionality
        env = os.environ.copy()
        lib_path = os.path.join(ROOT_DIR, "indi_driver", "lib")
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = lib_path + (os.pathsep + existing if existing else "")

        result = subprocess.run(
            ["python3", abort_script],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
            cwd=ROOT_DIR,
        )

        if result.returncode not in [0, 1]:
            raise Exception(
                f"Abort script test failed with exit code {result.returncode}"
            )

        print("   ✅ Abort script validation passed")

        # Validate configuration contains safety settings
        config = getattr(context, "app_config", {})
        if not config.get("hardware", {}).get("mock_mode", True):
            # Real hardware mode - ensure safety timeouts are set
            testing_config = config.get("testing", {})
            if testing_config.get("timeout_multiplier", 1.0) < 10:
                print("   ⚠️  Low timeout multiplier for hardware mode")

        print("   ✅ Safety configuration validated")

    except Exception as e:
        print(f"   ❌ Safety validation failed: {e}")
        raise


def _initialize_hardware_safety(context):
    """Initialize safety mechanisms for hardware mode."""
    try:
        # Ensure emergency stop is available
        if hasattr(context.dome, "emergency_stop"):
            print("   ✅ Emergency stop available")
        else:
            print("   ⚠️  Emergency stop method not found")

        # Ensure abort is available
        if hasattr(context.dome, "abort"):
            print("   ✅ Abort method available")
        else:
            print("   ⚠️  Abort method not found")

        # Initialize safety state tracking
        context.dome.safety_stop_requested = False
        context.dome.last_safety_check = time.time()

        # Add safety timeout tracking
        context.safety_timeout = (
            getattr(context, "timeout_multiplier", 30.0) * 10
        )  # 10x base timeout

        print("   🔒 Hardware safety mechanisms initialized")

    except Exception as e:
        print(f"   ⚠️  Safety initialization warning: {e}")
        # Don't fail scenario setup for safety init issues


def after_scenario(context, scenario):
    """Cleanup after each scenario with enhanced error recovery.

    Keep this hook extremely defensive to avoid any exceptions propagating
    to Behave that could cause a cleanup_error result. Enhanced for robust
    hardware error recovery and communication failure handling.
    """
    try:
        # Enhanced safety for hardware mode with retry logic
        if (
            hasattr(context, "dome")
            and getattr(context, "test_mode", "smoke") == "hardware"
        ):
            try:
                print("   🛑 Hardware mode: Executing enhanced safety cleanup...")

                # Multi-stage safety cleanup with retries
                _execute_enhanced_safety_cleanup(context)

            except Exception as e:
                # Log but never propagate cleanup issues
                print(f"   ⚠️  Hardware cleanup warning: {e}")

                # Final fallback - try direct abort script
                try:
                    _execute_fallback_abort(context)
                except Exception:
                    print(
                        "   ⚠️  Fallback abort also failed - "
                        "manual intervention may be needed"
                    )

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


def _execute_enhanced_safety_cleanup(context):
    """
    Execute enhanced safety cleanup with retry logic for hardware mode.

    Args:
        context: Behave context object
    """
    max_retries = 3

    for attempt in range(max_retries):
        try:
            # Primary safety cleanup
            if hasattr(context.dome, "emergency_stop"):
                context.dome.emergency_stop()
                print(f"   ✅ Emergency stop executed (attempt {attempt + 1})")

            # Additional hardware safety checks
            if hasattr(context.dome, "abort"):
                context.dome.abort()
                print(f"   ✅ Abort command executed (attempt {attempt + 1})")

            # Test communication is still working
            if hasattr(context.dome, "status"):
                try:
                    status = context.dome.status()
                    print(
                        "   ✅ Communication verified "
                        f"(attempt {attempt + 1}): {status}"
                    )
                    break  # Success - exit retry loop
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(
                            "   🔄 Communication check failed, "
                            f"retrying... ({e}): {status}"
                        )
                        time.sleep(0.5)
                        continue
                    else:
                        print(
                            "   ⚠️  Communication still failing "
                            f"after retries: {e}: {status}"
                        )
            else:
                break  # No status method available - consider successful

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"   🔄 Safety cleanup failed, retrying... ({e})")
                time.sleep(0.5)
                continue
            else:
                print(f"   ❌ Safety cleanup failed after {max_retries} attempts: {e}")
                raise  # Re-raise for fallback handling

    # Give hardware time to settle after successful cleanup
    time.sleep(1.0)


def _execute_fallback_abort(context):
    """
    Execute fallback abort using direct script execution.

    Args:
        context: Behave context object
    """
    import os
    import subprocess

    try:
        ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        abort_script = os.path.join(ROOT_DIR, "indi_driver", "scripts", "abort.py")

        if os.path.exists(abort_script):
            env = os.environ.copy()
            lib_path = os.path.join(ROOT_DIR, "indi_driver", "lib")
            existing = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = lib_path + (os.pathsep + existing if existing else "")

            result = subprocess.run(
                ["python3", abort_script],
                capture_output=True,
                text=True,
                timeout=5,
                env=env,
                cwd=ROOT_DIR,
            )

            if result.returncode == 0:
                print("   ✅ Fallback abort script executed successfully")
            else:
                print(
                    f"   ⚠️  Fallback abort script returned non-zero: {result.stderr}"
                )
        else:
            print("   ⚠️  Fallback abort script not found")

    except Exception as e:
        print(f"   ⚠️  Fallback abort failed: {e}")
        # Don't re-raise - this is the last resort


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
