#!/usr/bin/env python3
"""
Base Test Configuration Module

Provides shared test infrastructure and configuration to eliminate redundancy
across integration tests. Groups common functionality:
- Test environment setup
- Configuration creation
- Hardware/smoke mode detection
- Test cleanup
"""

import json
import os
import subprocess
import sys
import time
import unittest
from functools import wraps

# Add indi_driver/lib directory for imports (repo root)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "indi_driver", "lib"))


def requires_hardware_state(state=None, dependencies=None):
    """Decorator to mark tests with hardware state requirements and dependencies.

    Args:
        state: Required dome state ("homed", "any", "safe")
        dependencies: List of test methods that must complete first
    """

    def decorator(test_func):
        @wraps(test_func)
        def wrapper(self, *args, **kwargs):
            if self.is_hardware_mode:
                # Check and enforce dependencies
                if dependencies:
                    self._check_test_dependencies_explicit(dependencies)

                # Check and enforce state requirements
                if state == "homed":
                    self._ensure_dome_homed()
                elif state == "safe":
                    self._ensure_dome_safe_state()

            return test_func(self, *args, **kwargs)

        # Store metadata for dependency tracking
        wrapper._hardware_state = state
        wrapper._hardware_dependencies = dependencies or []
        wrapper._original_name = test_func.__name__

        return wrapper

    return decorator


def hardware_startup_sequence(short_movement=True, check_weather=True):
    """Decorator for hardware startup sequence tests.

    Args:
        short_movement: Whether to include short movement validation
        check_weather: Whether to perform weather safety checks
    """

    def decorator(test_func):
        @wraps(test_func)
        def wrapper(self, *args, **kwargs):
            if not self.is_hardware_mode:
                self.skipTest("Hardware startup sequence only runs in hardware mode")

            print(f"\n🚀 Hardware startup sequence: {test_func.__name__}")

            # Weather safety check
            if check_weather and not self._check_weather_safety():
                self.skipTest("Weather conditions unsafe for hardware testing")

            # Run the test
            result = test_func(self, *args, **kwargs)

            # Post-test short movement validation if requested
            if short_movement:
                movement_success = self._run_short_movement_test()
                if not movement_success:
                    self.fail("Post-test movement validation failed")

            return result

        return wrapper

    return decorator


def _check_weather_safety(self):
    """Check weather conditions for hardware testing safety."""
    rain_status = os.environ.get("WEATHER_RAINING", "true").lower()
    if rain_status in ["true", "1", "yes"]:
        print("🌧️  Rain detected - hardware testing may be limited")
        return True  # Still allow testing, but with restrictions
    return True


class BaseTestCase(unittest.TestCase):
    """Base test case with shared configuration and setup."""

    # Class-level test session state for hardware mode sequencing
    _hardware_session_state = {
        "dome_homed": False,
        "dome_position": None,
        "shutter_state": "unknown",
        "last_operation": None,
        "session_start_time": None,
        "test_sequence": [],
        "isolation_required": False,
    }

    # Test ordering for hardware mode (dependency graph)
    _test_dependencies = {
        "test_connect_script": [],  # No dependencies
        "test_status_script_output_format": [],  # No dependencies
        "test_disconnect_script": [],  # No dependencies
        "test_abort_script": [],  # No dependencies
        # Home-dependent tests (require dome to be homed first)
        "test_shutter_scripts": ["test_park_script"],  # Shutter needs home
        "test_goto_script": ["test_park_script"],  # Goto needs home reference
        "test_movement_scripts": [],  # Movement can work without home
        # Complex operations (require basic functions working)
        "test_park_script": ["test_connect_script"],  # Park needs connection
        "test_unpark_script": ["test_park_script"],  # Unpark after park
        # Calibration tests (require stable operations)
        "test_calibration_position_accuracy": ["test_park_script", "test_goto_script"],
        "test_calibration_home_repeatability": ["test_park_script"],
        "test_calibration_rotation_timing": ["test_movement_scripts"],
    }

    def setUp(self):
        """Set up test environment with shared configuration and sequencing."""
        # Common paths
        self.repo_root = REPO_ROOT
        self.scripts_dir = os.path.join(REPO_ROOT, "indi_driver", "scripts")
        self.lib_dir = os.path.join(REPO_ROOT, "indi_driver", "lib")

        # Environment setup
        self.env = os.environ.copy()
        existing = self.env.get("PYTHONPATH", "")
        self.env["PYTHONPATH"] = self.lib_dir + (
            os.pathsep + existing if existing else ""
        )
        self.cwd = REPO_ROOT

        # Test mode detection
        self.test_mode = os.environ.get("DOME_TEST_MODE", "smoke").lower()
        self.is_hardware_mode = self.test_mode == "hardware"

        # Hardware session initialization
        if self.is_hardware_mode:
            self._initialize_hardware_session()
            self._check_test_dependencies()

        # Timeout configuration
        if self.is_hardware_mode:
            self.script_timeout = 120  # 2 minutes for hardware operations
            self.movement_timeout = 180  # 3 minutes for movement operations
            print("⚡ Hardware mode detected - using extended timeouts")
        else:
            self.script_timeout = 10  # 10 seconds for smoke tests
            self.movement_timeout = 15  # 15 seconds max for smoke tests
            print("🔹 Smoke mode detected - using short timeouts")

        # Configuration management
        self._config_created = False
        self._config_path = os.path.join(self.cwd, "dome_config.json")

        if not os.path.exists(self._config_path):
            config_content = self._create_test_config()
            with open(self._config_path, "w") as f:
                json.dump(config_content, f)
            self._config_created = True

    def _initialize_hardware_session(self):
        """Initialize hardware test session state and perform pre-test validation."""
        session_state = self._hardware_session_state

        if session_state["session_start_time"] is None:
            session_state["session_start_time"] = time.time()
            print("🔧 Initializing hardware test session...")

            # Pre-test hardware safety validation
            self._perform_pre_test_validation()

            # Initial dome state assessment
            self._assess_initial_dome_state()

            print("✅ Hardware test session initialized")

    def _perform_pre_test_validation(self):
        """Perform comprehensive pre-test validation for hardware mode."""
        print("🔍 Performing pre-test hardware validation...")

        # Check abort script availability (critical safety requirement)
        abort_script = os.path.join(self.scripts_dir, "abort.py")
        if not os.path.exists(abort_script):
            raise Exception(f"Critical: Abort script missing: {abort_script}")

        # Test abort script functionality
        try:
            result = subprocess.run(
                ["python3", abort_script],
                capture_output=True,
                text=True,
                timeout=10,
                env=self.env,
                cwd=self.cwd,
            )
            if result.returncode not in [0, 1]:
                raise Exception(
                    f"Abort script test failed: exit code {result.returncode}"
                )
        except subprocess.TimeoutExpired:
            raise Exception("Abort script timeout - unsafe for testing")

        # Weather safety check (no shutter movement in rain)
        rain_status = os.environ.get("WEATHER_RAINING", "true").lower()
        if rain_status in ["true", "1", "yes"]:
            print(
                "🌧️  Rain detected - shutter operations will require user confirmation"
            )
            self._hardware_session_state["weather_rain"] = True
        else:
            self._hardware_session_state["weather_rain"] = False

        print("   ✅ Safety validation passed")

    def _assess_initial_dome_state(self):
        """Assess initial dome state for test sequencing."""
        try:
            # Get initial status via status script
            status_result = self._run_script_safely("status.py", timeout=30)
            if status_result.returncode == 0:
                # Parse status output
                lines = [
                    ln.strip() for ln in status_result.stdout.splitlines() if ln.strip()
                ]
                if lines:
                    status_line = lines[-1]
                    parts = status_line.split()
                    if len(parts) >= 3:
                        # Status format: "parked shutter azimuth"
                        parked_status = parts[0].lower() in ["true", "1"]
                        shutter_status = parts[1].lower() in ["true", "1"]
                        azimuth = float(parts[2])

                        self._hardware_session_state["dome_homed"] = parked_status
                        self._hardware_session_state["dome_position"] = azimuth
                        self._hardware_session_state["shutter_state"] = (
                            "open" if shutter_status else "closed"
                        )

                        print(
                            f"   📊 Initial state: Parked={parked_status}, "
                            f"Azimuth={azimuth:.1f}°, "
                            f"Shutter={'open' if shutter_status else 'closed'}"
                        )

        except Exception as e:
            print(f"   ⚠️  Could not assess initial dome state: {e}")
            # Continue with unknown state

    def _check_test_dependencies(self):
        """Check if current test has unmet dependencies in hardware mode."""
        test_name = self._testMethodName
        dependencies = self._test_dependencies.get(test_name, [])

        if dependencies:
            session_state = self._hardware_session_state
            completed_tests = set(session_state["test_sequence"])

            unmet_deps = [dep for dep in dependencies if dep not in completed_tests]
            if unmet_deps:
                print(f"⚠️  Test {test_name} has unmet dependencies: {unmet_deps}")
                print(f"   Completed tests: {list(completed_tests)}")

                # For critical dependencies, ensure they run first
                if "test_park_script" in unmet_deps and test_name in [
                    "test_shutter_scripts",
                    "test_goto_script",
                    "test_calibration_position_accuracy",
                ]:
                    print("   🏠 Running prerequisite homing sequence...")
                    self._ensure_dome_homed()

    def _ensure_dome_homed(self):
        """Ensure dome is homed before tests that require it."""
        session_state = self._hardware_session_state

        if not session_state["dome_homed"]:
            print("   🏠 Executing homing sequence...")
            try:
                # Run park script to home the dome
                park_result = self._run_script_safely(
                    "park.py", timeout=self.movement_timeout
                )
                if park_result.returncode == 0:
                    session_state["dome_homed"] = True
                    session_state["dome_position"] = 0.0
                    session_state["last_operation"] = "home"
                    print("   ✅ Dome homed successfully")
                else:
                    print(f"   ⚠️  Homing failed: {park_result.stderr}")

            except subprocess.TimeoutExpired:
                print(f"   ❌ Homing timed out after {self.movement_timeout}s")
                raise Exception("Unable to home dome - unsafe for dependent tests")

    def _check_test_dependencies_explicit(self, dependencies):
        """Check explicit test dependencies for decorated tests."""
        if not self.is_hardware_mode:
            return  # Dependencies only matter in hardware mode

        session_state = self._hardware_session_state
        completed_tests = set(session_state["test_sequence"])

        unmet_deps = [dep for dep in dependencies if dep not in completed_tests]
        if unmet_deps:
            print(f"⚠️  Explicit dependencies unmet: {unmet_deps}")
            raise Exception(f"Test dependencies not satisfied: {unmet_deps}")

    def _ensure_dome_safe_state(self):
        """Ensure dome is in a safe state for testing."""
        if not self.is_hardware_mode:
            return

        session_state = self._hardware_session_state

        # Check if dome needs to be returned to safe position
        if session_state.get("isolation_required", False):
            print("   🔒 Returning dome to safe state after isolation-required test...")
            try:
                # Run park to return to safe state
                park_result = self._run_script_safely(
                    "park.py", timeout=self.movement_timeout
                )
                if park_result.returncode == 0:
                    session_state["dome_homed"] = True
                    session_state["dome_position"] = 0.0
                    session_state["isolation_required"] = False
                    print("   ✅ Dome returned to safe state")
                else:
                    print(
                        f"   ⚠️  Could not return to safe state: {park_result.stderr}"
                    )
            except subprocess.TimeoutExpired:
                print(f"   ❌ Safe state timeout after {self.movement_timeout}s")

    def _check_weather_safety(self):
        """Check weather conditions for hardware testing safety."""
        rain_status = os.environ.get("WEATHER_RAINING", "true").lower()
        if rain_status in ["true", "1", "yes"]:
            print("🌧️  Rain detected - hardware testing may be limited")
            return True  # Still allow testing, but with restrictions
        return True

    def _create_test_config(self):
        """Create shared test configuration based on test mode."""
        base_config = {
            "pins": {
                "encoder_a": 1,
                "encoder_b": 5,
                "home_switch": 2,
                "shutter_upper_limit": 1,
                "shutter_lower_limit": 2,
                "dome_rotate": 1,
                "dome_direction": 2,
                "shutter_move": 1,
                "shutter_direction": 2,
            },
            "calibration": {
                "home_position": 0,
                "ticks_to_degrees": 1.0,
                "poll_interval": 0.1,
            },
            "testing": {
                "smoke_test_timeout": 1.0 if not self.is_hardware_mode else 30.0,
                "timeout_multiplier": 30.0 if self.is_hardware_mode else 1.0,
                "hardware_mode": self.is_hardware_mode,
                "smoke_test": not self.is_hardware_mode,
                "short_movement_duration": 2.0,  # For initial hardware testing
                "min_movement_timeout": 5.0,  # Minimum timeout for safety
            },
        }

        # Add safety configuration for safety tests
        if hasattr(self, "_needs_safety_config") and self._needs_safety_config:
            base_config["safety"] = {
                "emergency_stop_timeout": 2.0,
                "operation_timeout": 30.0 if self.is_hardware_mode else 5.0,
                "max_rotation_time": 120.0 if self.is_hardware_mode else 10.0,
                "max_shutter_time": 60.0 if self.is_hardware_mode else 5.0,
            }

        if self.is_hardware_mode:
            # Hardware mode configuration
            base_config["hardware"] = {"mock_mode": False, "device_port": 0}
            print("   🔧 Created hardware mode configuration")
        else:
            # Smoke test configuration
            base_config["hardware"] = {"mock_mode": True, "device_port": 0}
            print("   🔧 Created smoke test configuration")

        return base_config

    def tearDown(self):
        """Enhanced cleanup for hardware mode with shared safety and session
        tracking.
        """
        try:
            # Track test completion for sequencing
            if self.is_hardware_mode:
                test_name = self._testMethodName
                session_state = self._hardware_session_state

                # Record test completion
                if test_name not in session_state["test_sequence"]:
                    session_state["test_sequence"].append(test_name)

                # Update dome state after test
                self._update_dome_state_after_test()

                # Execute safety cleanup for hardware mode
                print("🛑 Executing hardware safety cleanup...")
                abort_script = os.path.join(self.scripts_dir, "abort.py")
                if os.path.exists(abort_script):
                    try:
                        subprocess.run(
                            ["python3", abort_script],
                            timeout=5,
                            env=self.env,
                            cwd=self.cwd,
                        )
                        print("   ✅ Emergency stop executed")
                    except Exception as e:
                        print(f"   ⚠️ Emergency stop warning: {e}")

            # Clean up temporary config if we created it
            if self._config_created and os.path.exists(self._config_path):
                os.remove(self._config_path)
        except Exception as e:
            print(f"⚠️ Warning during test cleanup: {e}")

    def _update_dome_state_after_test(self):
        """Update session state based on test that just completed."""
        test_name = self._testMethodName
        session_state = self._hardware_session_state

        # Update state based on test type
        if "park" in test_name:
            session_state["dome_homed"] = True
            session_state["dome_position"] = 0.0
            session_state["last_operation"] = "park"
        elif "goto" in test_name:
            session_state["last_operation"] = "goto"
        elif "movement" in test_name or "move_" in test_name:
            session_state["last_operation"] = "movement"
            session_state["dome_homed"] = False  # Movement may disturb home
        elif "shutter" in test_name:
            session_state["last_operation"] = "shutter"

        session_state["isolation_required"] = test_name in [
            "test_calibration_position_accuracy",
            "test_calibration_home_repeatability",
            "test_calibration_rotation_timing",
        ]

    def _run_script_safely(self, script_name, args=None, timeout=None):
        """Run a script with common error handling and appropriate timeouts."""
        if args is None:
            args = []
        if timeout is None:
            timeout = self.script_timeout

        script_path = os.path.join(self.scripts_dir, script_name)

        return subprocess.run(
            ["python3", script_path] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=self.env,
            cwd=self.cwd,
        )

    def _check_shutter_weather_safety(self, operation_name):
        """Check weather safety for shutter operations.

        Args:
            operation_name: Name of the operation (for user confirmation)

        Returns:
            bool: True if operation is safe to proceed
        """
        session_state = self._hardware_session_state

        if not session_state.get("weather_rain", False):
            return True  # No rain, safe to proceed

        # Rain detected - check for user confirmation
        if operation_name in ["open", "shutter"]:
            confirmation = os.environ.get("SHUTTER_RAIN_OVERRIDE", "").lower()
            if confirmation in ["true", "1", "yes", "confirmed"]:
                print(f"🌧️  Rain override confirmed for {operation_name}")
                return True
            else:
                print(
                    "🌧️  Blocking "
                    + operation_name
                    + " - rain detected and no override"
                )
                print("     Set SHUTTER_RAIN_OVERRIDE=true to force shutter operations")
                return False

        # Rotation is safe in rain
        return True

    def _run_short_movement_test(self, direction="cw", duration=2.0):
        """Run a short movement test for initial hardware validation.

        Args:
            direction: "cw" or "ccw" for clockwise/counter-clockwise
            duration: Duration in seconds (default 2.0 for safety)

        Returns:
            bool: True if movement test succeeded
        """
        if not self.is_hardware_mode:
            print("🔹 Short movement test skipped in smoke mode")
            return True

        print(f"🔄 Running short {direction.upper()} movement test ({duration}s)...")
        print(
            f"   # when user performs this step, the dome should rotate for "
            f"{duration} seconds in the {direction.upper()} direction"
        )

        try:
            # Start movement
            move_script = f"move_{direction}.py"
            start_time = time.time()

            # Start movement in background
            move_process = subprocess.Popen(
                ["python3", os.path.join(self.scripts_dir, move_script)],
                env=self.env,
                cwd=self.cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Let it run for specified duration
            time.sleep(duration)

            # Stop movement
            abort_result = self._run_script_safely("abort.py", timeout=5)

            # Wait for move process to complete
            try:
                move_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                move_process.terminate()

            elapsed = time.time() - start_time

            if abort_result.returncode == 0:
                print(f"   ✅ Short movement completed in {elapsed:.1f}s")
                return True
            else:
                print(f"   ⚠️  Movement stop failed: {abort_result.stderr}")
                return False

        except Exception as e:
            print(f"   ❌ Short movement test failed: {e}")
            # Emergency stop attempt
            try:
                self._run_script_safely("abort.py", timeout=5)
            except Exception:
                pass
            return False

    def _capture_calibration_data(
        self, operation, expected_result, actual_result, timing_data=None
    ):
        """Capture calibration data for hardware validation.

        Args:
            operation: Description of operation performed
            expected_result: Expected position/state
            actual_result: Actual position/state achieved
            timing_data: Optional dict with timing measurements
        """
        if not self.is_hardware_mode:
            return  # Only capture data in hardware mode

        calibration_log = getattr(self, "_calibration_log", [])

        entry = {
            "timestamp": time.time(),
            "operation": operation,
            "expected": expected_result,
            "actual": actual_result,
            "error": (
                abs(actual_result - expected_result)
                if isinstance(actual_result, (int, float))
                else None
            ),
        }

        if timing_data:
            entry["timing"] = timing_data

        calibration_log.append(entry)
        self._calibration_log = calibration_log

        # Log to console for immediate feedback
        if entry["error"] is not None:
            print(f"📊 Calibration: {operation} - Error: {entry['error']:.2f}°")
        else:
            print(f"📊 Calibration: {operation} - Logged")

    def _measure_operation_timing(self, operation_func, *args, **kwargs):
        """Measure timing for an operation and return result with timing data.

        Returns:
            tuple: (operation_result, timing_dict)
        """
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        end_time = time.time()

        timing_data = {
            "duration": end_time - start_time,
            "start_time": start_time,
            "end_time": end_time,
        }

        return result, timing_data


class BaseINDIScriptTestCase(BaseTestCase):
    """Base class for INDI script tests with script-specific functionality."""

    def setUp(self):
        """Set up INDI script test environment."""
        super().setUp()

        # INDI script list
        self.required_scripts = [
            "connect.py",
            "disconnect.py",
            "status.py",
            "open.py",
            "close.py",
            "park.py",
            "unpark.py",
            "goto.py",
            "move_cw.py",
            "move_ccw.py",
            "abort.py",
        ]

    def _basic_config_validation(self):
        """Basic configuration validation using existing infrastructure."""
        print("\n🔍 Running basic configuration validation...")

        # Use existing config loading infrastructure
        try:
            from config import load_config

            config = load_config()
        except ImportError:
            # Fallback if config module not available
            print("   ⚠️  Config module not available, using basic validation")
            config = self._create_test_config()

        # Basic validation for hardware mode only
        if self.is_hardware_mode:
            self.assertIn("hardware", config, "Hardware section required")
            hardware = config["hardware"]
            self.assertFalse(
                hardware.get("mock_mode", True),
                "Hardware mode requires mock_mode: false",
            )
            print("   ✅ Hardware configuration validation passed")
        else:
            print("   ✅ Mock mode - no additional validation needed")


class BaseSafetyTestCase(BaseTestCase):
    """Base class for safety system tests."""

    def setUp(self):
        """Set up safety test environment."""
        self._needs_safety_config = True  # Flag for enhanced config
        super().setUp()

    def _create_test_config(self):
        """Create safety test configuration with enhanced safety settings."""
        config = super()._create_test_config()

        # Add safety-specific configuration
        config["safety"] = {
            "emergency_stop_timeout": 2.0,
            "operation_timeout": 30.0 if self.is_hardware_mode else 5.0,
            "max_rotation_time": 120.0 if self.is_hardware_mode else 10.0,
            "max_shutter_time": 60.0 if self.is_hardware_mode else 5.0,
        }

        # Enhanced testing configuration for safety
        config["testing"].update(
            {
                "timeout_multiplier": 30.0 if self.is_hardware_mode else 1.0,
            }
        )

        return config
