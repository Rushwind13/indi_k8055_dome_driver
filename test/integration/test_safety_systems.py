#!/usr/bin/env python3
"""
Safety Systems Integration Tests

This test suite validates that all safety mechanisms work correctly
in both smoke and hardware modes. These tests ensure:

1. Emergency stop functionality works correctly
2. Abort commands stop all operations immediately
3. Safety timeouts prevent runaway operations
4. Hardware safety validation occurs before tests
5. Test teardown includes proper safety cleanup
"""

import os
import subprocess
import sys
import time
import unittest

# Add indi_driver/lib directory for imports (repo root)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "indi_driver", "lib"))

from dome import Dome  # noqa: E402
from test_base import BaseSafetyTestCase  # noqa: E402


class TestSafetySystems(BaseSafetyTestCase):
    """Test suite for safety system functionality."""

    def test_abort_script_availability(self):
        """Test that abort script exists and is executable."""
        abort_script = os.path.join(self.scripts_dir, "abort.py")

        # Script must exist
        self.assertTrue(os.path.exists(abort_script), "Abort script must exist")

        # Script must be executable
        self.assertTrue(
            os.access(abort_script, os.X_OK), "Abort script must be executable"
        )

    def test_abort_script_functionality(self):
        """Test that abort script executes successfully."""
        abort_script = os.path.join(self.scripts_dir, "abort.py")

        # Test abort script execution
        result = subprocess.run(
            ["python3", abort_script],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.cwd,
            timeout=10 if not self.is_hardware_mode else 30,
        )

        # Abort should never fail (exit code 0)
        self.assertEqual(result.returncode, 0, f"Abort script failed: {result.stderr}")

        if self.is_hardware_mode:
            print("⚡ Hardware abort test completed successfully")

    def test_emergency_stop_response_time(self):
        """Test emergency stop response time is acceptable."""
        abort_script = os.path.join(self.scripts_dir, "abort.py")

        # Measure abort script execution time
        start_time = time.time()
        result = subprocess.run(
            ["python3", abort_script],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.cwd,
            timeout=5,
        )
        end_time = time.time()

        execution_time = end_time - start_time

        # Emergency stop should complete quickly
        max_response_time = 3.0 if self.is_hardware_mode else 1.0
        self.assertLess(
            execution_time,
            max_response_time,
            f"Emergency stop took {execution_time}s (max: {max_response_time}s)",
        )

        # Should still succeed
        self.assertEqual(result.returncode, 0)

    def test_safety_timeout_configuration(self):
        """Test that safety timeouts are properly configured."""
        from config import load_config

        config = load_config()

        # Safety timeouts should exist
        safety_config = config.get("safety", {})

        # Check for essential safety timeouts
        essential_timeouts = [
            "emergency_stop_timeout",
            "operation_timeout",
            "max_rotation_time",
            "max_shutter_time",
        ]

        for timeout_key in essential_timeouts:
            self.assertIn(
                timeout_key, safety_config, f"Missing safety timeout: {timeout_key}"
            )
            timeout_value = safety_config[timeout_key]
            self.assertIsInstance(
                timeout_value, (int, float), f"Timeout {timeout_key} must be numeric"
            )
            self.assertGreater(
                timeout_value, 0, f"Timeout {timeout_key} must be positive"
            )

    def test_hardware_mode_safety_validation(self):
        """Test hardware mode safety validation works."""
        if not self.is_hardware_mode:
            self.skipTest(
                "Hardware mode safety validation only applies to hardware mode"
            )

        # This test verifies that hardware mode includes proper safety checks
        # The safety validation should have run during setUp

        # Verify abort script is available (critical for hardware safety)
        abort_script = os.path.join(self.scripts_dir, "abort.py")
        self.assertTrue(os.path.exists(abort_script))

        # Verify configuration has hardware safety settings
        from config import load_config

        config = load_config()

        # Hardware mode should have mock_mode = False
        self.assertEqual(config.get("hardware", {}).get("mock_mode"), False)

        # Safety timeouts should be longer for hardware mode
        safety_config = config.get("safety", {})
        operation_timeout = safety_config.get("operation_timeout", 0)
        self.assertGreaterEqual(
            operation_timeout, 20, "Hardware mode needs longer safety timeouts"
        )

    def test_smoke_mode_safety_validation(self):
        """Test smoke mode safety validation works."""
        if self.is_hardware_mode:
            self.skipTest("Smoke mode safety validation only applies to smoke mode")

        # Verify configuration has smoke mode settings
        from config import load_config

        config = load_config()

        # Smoke mode should have mock_mode = True
        self.assertEqual(config.get("hardware", {}).get("mock_mode"), True)

        # Safety timeouts should be shorter for smoke mode
        safety_config = config.get("safety", {})
        operation_timeout = safety_config.get("operation_timeout", 0)
        self.assertLessEqual(
            operation_timeout, 10, "Smoke mode should have shorter safety timeouts"
        )

    def test_sequential_abort_calls(self):
        """Test that multiple abort calls work correctly."""
        abort_script = os.path.join(self.scripts_dir, "abort.py")

        # Call abort multiple times in succession
        for i in range(3):
            result = subprocess.run(
                ["python3", abort_script],
                capture_output=True,
                text=True,
                env=self.env,
                cwd=self.cwd,
                timeout=5,
            )

            # Each call should succeed
            self.assertEqual(
                result.returncode, 0, f"Abort call {i+1} failed: {result.stderr}"
            )

    def test_abort_during_operation(self):
        """Test abort functionality during dome operations."""
        # Start a rotation or movement
        move_cw_script = os.path.join(self.scripts_dir, "move_cw.py")
        abort_script = os.path.join(self.scripts_dir, "abort.py")

        if not os.path.exists(move_cw_script):
            self.skipTest("move_cw.py script not found")

        # Start movement (non-blocking)
        move_process = subprocess.Popen(
            ["python3", move_cw_script], env=self.env, cwd=self.cwd
        )

        try:
            # Give movement a moment to start
            time.sleep(0.1 if not self.is_hardware_mode else 1.0)

            # Send abort command
            abort_result = subprocess.run(
                ["python3", abort_script],
                capture_output=True,
                text=True,
                env=self.env,
                cwd=self.cwd,
                timeout=5,
            )

            # Abort should succeed
            self.assertEqual(abort_result.returncode, 0)

            # Wait for movement process to finish
            move_process.wait(timeout=5)

        finally:
            # Ensure movement process is terminated
            try:
                move_process.terminate()
                move_process.wait(timeout=2)
            except Exception:
                pass


def run_safety_tests():
    """Run the safety system test suite."""
    print("=" * 60)
    print("DOME SAFETY SYSTEMS VALIDATION")
    print("=" * 60)
    print()
    print("Testing safety mechanisms and emergency procedures...")
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test class
    suite.addTests(loader.loadTestsFromTestCase(TestSafetySystems))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print()
    print("=" * 60)
    print("SAFETY SYSTEMS VALIDATION SUMMARY")
    print("=" * 60)

    if result.wasSuccessful():
        print("✅ ALL SAFETY SYSTEMS VALIDATED SUCCESSFULLY")
        print()
        print("Safety mechanisms are working correctly:")
        print("  • Emergency stop functionality verified")
        print("  • Abort commands respond within time limits")
        print("  • Safety timeouts are properly configured")
        print("  • Hardware safety validation working")
        print("  • Test teardown includes safety cleanup")
        print()
        return True
    else:
        print("❌ SAFETY VALIDATION FAILED")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print()
        print(
            "⚠️  CRITICAL: Do not proceed with hardware testing "
            "until safety issues are resolved!"
        )
        return False


if __name__ == "__main__":
    success = run_safety_tests()
    sys.exit(0 if success else 1)
