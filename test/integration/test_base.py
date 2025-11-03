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
import unittest

# Add indi_driver/lib directory for imports (repo root)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "indi_driver", "lib"))


class BaseTestCase(unittest.TestCase):
    """Base test case with shared configuration and setup."""

    def setUp(self):
        """Set up test environment with shared configuration."""
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
        """Enhanced cleanup for hardware mode with shared safety."""
        try:
            # Execute safety cleanup for hardware mode
            if self.is_hardware_mode:
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
        from config import load_config

        config = load_config()

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
