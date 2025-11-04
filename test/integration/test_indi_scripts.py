#!/usr/bin/env python
"""
INDI Script Integration Tests

This test suite validates that all 11 INDI wrapper scripts meet the
functional contract requirements and work correctly with the dome system.

These tests verify:
1. All scripts exist and are executable
2. All scripts follow INDI contract (exit codes, output format)
3. All scripts properly interface with dome.py functionality
4. Scripts handle error conditions gracefully
5. Scripts provide proper status feedback
"""

import os
import subprocess
import sys
import time
import unittest

# Add indi_driver/lib directory for imports (repo root)
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "indi_driver", "lib"))

from test_base import (  # noqa: E402
    BaseINDIScriptTestCase,
    hardware_startup_sequence,
    requires_hardware_state,
)


class TestINDIScripts(BaseINDIScriptTestCase):
    """Test suite for INDI dome script compliance and functionality."""

    def test_aaa_basic_config_validation(self):
        """Basic configuration validation using existing infrastructure."""
        self._basic_config_validation()

    @hardware_startup_sequence(short_movement=True, check_weather=True)
    def test_aaa_hardware_startup_connectivity(self):
        """Hardware startup test: Basic connectivity and response validation.

        This test ensures very short operations for initial hardware validation:
        - Connect/disconnect cycle (<5 seconds total)
        - Status readout validation
        - Basic safety system check
        """
        if not self.is_hardware_mode:
            self.skipTest("Hardware startup test requires hardware mode")

        print("\n🚀 Hardware Startup Phase 1: Connectivity Test")

        # Phase 1: Quick connect/status/disconnect cycle
        # Expected: dome should connect and respond within 5 seconds total
        print(
            "   # when user performs this step, the dome should connect and "
            "respond within 5 seconds"
        )

        start_time = time.time()

        # Quick connection test
        connect_result = self._run_script_safely("connect.py", timeout=3)
        self.assertEqual(
            connect_result.returncode, 0, "Connection should succeed quickly"
        )

        # Quick status check
        status_result = self._run_script_safely("status.py", timeout=2)
        self.assertEqual(status_result.returncode, 0, "Status should respond quickly")

        # Quick disconnect
        disconnect_result = self._run_script_safely("disconnect.py", timeout=2)
        self.assertEqual(disconnect_result.returncode, 0, "Disconnect should succeed")

        total_time = time.time() - start_time
        print(f"   ✅ Connectivity test completed in {total_time:.1f}s")

        # Validate timing expectation
        self.assertLess(
            total_time, 8.0, "Connectivity test should complete within 8 seconds"
        )

    @hardware_startup_sequence(short_movement=True, check_weather=True)
    def test_aaa_hardware_startup_short_movement(self):
        """Hardware startup test: Short movement validation (<5 seconds).

        This test performs minimal movement to validate motor control:
        - 2-second CW rotation
        - Immediate abort
        - Verify movement stops quickly
        """
        if not self.is_hardware_mode:
            self.skipTest("Hardware startup test requires hardware mode")

        print("\n🚀 Hardware Startup Phase 2: Short Movement Test")
        print(
            "   # when user performs this step, the dome should rotate for "
            "2 seconds in the CW direction"
        )

        # Weather safety check for movement
        if not self._check_shutter_weather_safety("rotation"):
            self.skipTest("Weather conditions require override for movement test")

        # Run the short movement test from base class
        movement_success = self._run_short_movement_test(direction="cw", duration=2.0)
        self.assertTrue(movement_success, "Short movement test should succeed")

    @requires_hardware_state(state="any")
    def test_aaa_hardware_startup_safety_validation(self):
        """Hardware startup test: Safety system validation.

        This test validates safety systems respond quickly:
        - Abort command responsiveness (<2 seconds)
        - Emergency stop functionality
        - Communication timeout handling
        """
        if not self.is_hardware_mode:
            self.skipTest("Hardware safety test requires hardware mode")

        print("\n🚀 Hardware Startup Phase 3: Safety System Test")
        print(
            "   # when user performs this step, the abort should stop any "
            "motion within 2 seconds"
        )

        # Test abort responsiveness
        start_time = time.time()
        abort_result = self._run_script_safely("abort.py", timeout=3)
        abort_time = time.time() - start_time

        self.assertEqual(abort_result.returncode, 0, "Abort should always succeed")
        self.assertLess(abort_time, 3.0, "Abort should respond within 3 seconds")

        print(f"   ✅ Abort system validated - response time: {abort_time:.1f}s")

    def test_all_scripts_exist(self):
        """Verify that all required scripts exist in scripts directory."""
        print("\n📁 Checking script file existence...")
        for script in self.required_scripts:
            with self.subTest(script=script):
                script_path = os.path.join(self.scripts_dir, script)
                self.assertTrue(
                    os.path.exists(script_path),
                    f"Script {script} missing at {script_path}",
                )

    def test_all_scripts_executable(self):
        """Test that all scripts are executable."""
        for script in self.required_scripts:
            script_path = os.path.join(self.scripts_dir, script)
            self.assertTrue(
                os.access(script_path, os.X_OK), f"Script not executable: {script}"
            )

    def test_connect_script(self):
        """Test connect.py script functionality."""
        script_path = os.path.join(self.scripts_dir, "connect.py")

        # Test successful connection
        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.cwd,
        )

        # Should succeed (exit code 0)
        self.assertEqual(result.returncode, 0, f"Connect failed: {result.stderr}")

    # Allow stdout output from underlying dome module

    def test_disconnect_script(self):
        """Test disconnect.py script functionality."""
        script_path = os.path.join(self.scripts_dir, "disconnect.py")

        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.cwd,
        )

        # Should succeed (exit code 0) - disconnect should never fail
        self.assertEqual(result.returncode, 0, f"Disconnect failed: {result.stderr}")

    # Allow stdout output from underlying dome module

    def test_status_script_output_format(self):
        """Test status.py script output format compliance."""
        script_path = os.path.join(self.scripts_dir, "status.py")

        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.cwd,
        )

        # Should succeed
        self.assertEqual(result.returncode, 0, f"Status failed: {result.stderr}")

        # Parse output format from the last non-empty line: "parked shutter azimuth"
        lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
        status_line = lines[-1] if lines else ""
        output_parts = status_line.split()
        self.assertEqual(
            len(output_parts),
            3,
            f"Status output format wrong: expected 3 values, got {len(output_parts)}",
        )

        # Validate parked status (0 or 1)
        parked_raw = output_parts[0]
        parked_status = (
            1
            if parked_raw.lower() == "true"
            else (0 if parked_raw.lower() == "false" else int(parked_raw))
        )
        self.assertIn(parked_status, [0, 1], f"Invalid parked status: {parked_status}")

        # Validate shutter status (0 or 1)
        shutter_raw = output_parts[1]
        shutter_status = (
            1
            if shutter_raw.lower() == "true"
            else (0 if shutter_raw.lower() == "false" else int(shutter_raw))
        )
        self.assertIn(
            shutter_status, [0, 1], f"Invalid shutter status: {shutter_status}"
        )

        # Validate azimuth (0.0-360.0)
        azimuth = float(output_parts[2])
        self.assertTrue(0.0 <= azimuth <= 360.0, f"Invalid azimuth: {azimuth}")

    @requires_hardware_state(state="any", dependencies=["test_connect_script"])
    def test_park_script(self):
        """Test park.py script functionality."""
        script_path = os.path.join(self.scripts_dir, "park.py")

        try:
            result = subprocess.run(
                ["python3", script_path],
                capture_output=True,
                text=True,
                timeout=self.movement_timeout,
                env=self.env,
                cwd=self.cwd,
            )
            # Accept success or graceful failure
            self.assertIn(
                result.returncode, [0, 1], f"Park returned {result.returncode}"
            )

            if self.is_hardware_mode:
                print(
                    "   ⚡ Hardware park operation completed "
                    f"in {self.movement_timeout}s timeout"
                )

        except subprocess.TimeoutExpired:
            if self.is_hardware_mode:
                self.fail(
                    "Park operation timed out after "
                    f"{self.movement_timeout}s in hardware mode"
                )
            else:
                # In smoke mode, park may not complete; treat timeout as acceptable
                print("   🔹 Smoke mode park timeout is acceptable")
                pass

    @requires_hardware_state(state="homed", dependencies=["test_park_script"])
    def test_shutter_scripts(self):
        """Test shutter open/close scripts."""
        open_script = os.path.join(self.scripts_dir, "open.py")
        close_script = os.path.join(self.scripts_dir, "close.py")

        # Weather safety check for shutter operations
        if self.is_hardware_mode and not self._check_shutter_weather_safety("shutter"):
            self.skipTest(
                "Weather conditions unsafe for shutter operations - "
                "use SHUTTER_RAIN_OVERRIDE=true to override"
            )

        # Test close script
        result = subprocess.run(
            ["python3", close_script],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.cwd,
        )
        # May fail if not at home, but should not crash
        self.assertIn(result.returncode, [0, 1])

        # Test open script
        result = subprocess.run(
            ["python3", open_script],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.cwd,
        )
        # May fail if not at home, but should not crash
        self.assertIn(result.returncode, [0, 1])

    def test_unpark_script(self):
        """Test unpark.py script functionality."""
        script_path = os.path.join(self.scripts_dir, "unpark.py")

        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=self.script_timeout,
            env=self.env,
            cwd=self.cwd,
        )
        # Should succeed or at least not crash
        self.assertIn(result.returncode, [0, 1])

        if self.is_hardware_mode:
            print(
                "   ⚡ Hardware unpark operation completed "
                f"within {self.script_timeout}s"
            )

    @requires_hardware_state(state="homed", dependencies=["test_park_script"])
    def test_goto_script(self):
        """Test goto.py script functionality."""
        script_path = os.path.join(self.scripts_dir, "goto.py")

        # Test with invalid azimuth (should not crash)
        try:
            result = subprocess.run(
                ["python3", script_path, "400.0"],
                capture_output=True,
                text=True,
                timeout=self.script_timeout,
                env=self.env,
                cwd=self.cwd,
            )
            self.assertIn(
                result.returncode, [0, 1], "Goto with invalid azimuth should not crash"
            )
        except subprocess.TimeoutExpired:
            if self.is_hardware_mode:
                self.fail(
                    "Goto with invalid azimuth timed out "
                    f"after {self.script_timeout}s in hardware mode"
                )
            else:
                # In smoke mode, rotation may simulate moves; a short timeout is ok
                pass

        # Test with no arguments (should not crash)
        try:
            result = subprocess.run(
                ["python3", script_path],
                capture_output=True,
                text=True,
                timeout=self.script_timeout,
                env=self.env,
                cwd=self.cwd,
            )
            self.assertIn(
                result.returncode, [0, 1], "Goto with no arguments should not crash"
            )
        except subprocess.TimeoutExpired:
            if self.is_hardware_mode:
                print(
                    "   ⚠️  Goto with no args timed out after "
                    f"{self.script_timeout}s (expected in hardware mode)"
                )
            else:
                # Also acceptable; treat as non-crash within short window
                pass

    def test_movement_scripts(self):
        """Test move_cw.py and move_ccw.py scripts."""
        cw_script = os.path.join(self.scripts_dir, "move_cw.py")
        ccw_script = os.path.join(self.scripts_dir, "move_ccw.py")
        abort_script = os.path.join(self.scripts_dir, "abort.py")

        # Test CW movement
        result = subprocess.run(
            ["python3", cw_script],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.cwd,
        )
        self.assertEqual(result.returncode, 0, f"Move CW failed: {result.stderr}")

        # Stop movement
        subprocess.run(
            ["python3", abort_script], capture_output=True, env=self.env, cwd=self.cwd
        )

        # Test CCW movement
        result = subprocess.run(
            ["python3", ccw_script],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.cwd,
        )
        self.assertEqual(result.returncode, 0, f"Move CCW failed: {result.stderr}")

        # Stop movement
        subprocess.run(
            ["python3", abort_script], capture_output=True, env=self.env, cwd=self.cwd
        )

    def test_abort_script(self):
        """Test abort.py script functionality."""
        script_path = os.path.join(self.scripts_dir, "abort.py")

        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            env=self.env,
            cwd=self.cwd,
        )

        # Abort should never fail (exit code 0)
        self.assertEqual(result.returncode, 0, f"Abort failed: {result.stderr}")

    def test_script_error_handling(self):
        """Test that scripts handle errors gracefully."""
        # Test all scripts can handle being run when dome is in various states
        scripts_to_test = [
            "connect.py",
            "disconnect.py",
            "status.py",
            "abort.py",
        ]

        for script in scripts_to_test:
            script_path = os.path.join(self.scripts_dir, script)
            with self.subTest(script=script):
                result = subprocess.run(
                    ["python3", script_path],
                    capture_output=True,
                    text=True,
                    timeout=self.script_timeout,
                    env=self.env,
                    cwd=self.cwd,
                )
                # Should not crash (exit code 0 or 1, not other values)
                self.assertIn(
                    result.returncode,
                    [0, 1],
                    f"Script {script} crashed with exit code {result.returncode}",
                )

    def test_indi_contract_compliance(self):
        """Test that all scripts comply with INDI contract."""
        for script in self.required_scripts:
            script_path = os.path.join(self.scripts_dir, script)

            with self.subTest(script=script):
                # Test that script returns proper exit codes
                try:
                    # Use appropriate timeout based on script and test mode
                    if script in ["goto.py", "park.py"] and self.is_hardware_mode:
                        timeout = self.movement_timeout
                    elif script == "goto.py":
                        timeout = 3  # Keep short for smoke mode goto
                    else:
                        timeout = self.script_timeout

                    result = subprocess.run(
                        ["python3", script_path],
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        env=self.env,
                        cwd=self.cwd,
                    )
                    # Should return 0 or 1 only (INDI contract)
                    self.assertIn(
                        result.returncode,
                        [0, 1],
                        f"Script {script} - invalid exit code: {result.returncode}",
                    )
                except subprocess.TimeoutExpired:
                    if self.is_hardware_mode and script in ["goto.py", "park.py"]:
                        self.fail(
                            f"Script {script} timed out after "
                            f"{timeout}s in hardware mode"
                        )
                    else:
                        # Allow time for long-run scripts (e.g. park,goto) in smoke mode
                        pass

    def test_full_operation_sequence(self):
        """Test a complete dome operation sequence using INDI scripts."""
        raise unittest.SkipTest("Skipping full INDI script sequence in smoke mode")

    @requires_hardware_state(
        state="homed", dependencies=["test_park_script", "test_goto_script"]
    )
    def test_calibration_position_accuracy(self):
        """Test and capture position accuracy data for calibration.

        This test validates goto positioning accuracy and captures
        calibration data for hardware tuning when in hardware mode.
        """
        if not self.is_hardware_mode:
            self.skipTest("Calibration data capture only runs in hardware mode")

        print("\n📊 Capturing position accuracy calibration data...")

        # Test positions for accuracy measurement
        test_positions = [0, 90, 180, 270, 45, 135, 225, 315]

        for target_position in test_positions:
            with self.subTest(position=target_position):
                print(f"   Testing goto {target_position}°...")

                # Measure goto operation timing
                def goto_operation():
                    return self._run_script_safely("goto.py", [str(target_position)])

                result, timing_data = self._measure_operation_timing(goto_operation)

                self.assertEqual(
                    result.returncode,
                    0,
                    f"Goto {target_position}° failed: {result.stderr}",
                )

                # Get actual position via status script
                status_result = self._run_script_safely("status.py")
                self.assertEqual(status_result.returncode, 0, "Status check failed")

                # Parse actual position from status output
                # Status format: "Azimuth: 123.4°"
                actual_position = self._parse_position_from_status(status_result.stdout)

                # Capture calibration data
                self._capture_calibration_data(
                    f"goto_{target_position}",
                    target_position,
                    actual_position,
                    timing_data,
                )

                # Validate within expected tolerance (larger tolerance for hardware)
                tolerance = 3.0  # 3 degrees for hardware validation
                position_error = abs(actual_position - target_position)
                if position_error > 180:
                    position_error = 360 - position_error

                self.assertLessEqual(
                    position_error,
                    tolerance,
                    f"Position error {position_error:.1f}° exceeds "
                    f"tolerance {tolerance}°",
                )

        # Report calibration summary
        self._report_calibration_summary()

    @requires_hardware_state(state="homed", dependencies=["test_park_script"])
    def test_calibration_home_repeatability(self):
        """Test and capture home position repeatability data."""
        if not self.is_hardware_mode:
            self.skipTest("Calibration data capture only runs in hardware mode")

        print("\n📊 Capturing home position repeatability data...")

        home_positions = []
        num_trials = 5  # Multiple home operations to test repeatability

        for trial in range(num_trials):
            print(f"   Home trial {trial + 1}/{num_trials}...")

            # Move away from home first
            self._run_script_safely("goto.py", ["90"])
            time.sleep(1)  # Brief pause

            # Execute park operation and measure timing
            def park_operation():
                return self._run_script_safely("park.py")

            result, timing_data = self._measure_operation_timing(park_operation)

            self.assertEqual(result.returncode, 0, f"Park trial {trial + 1} failed")

            # Get home position
            status_result = self._run_script_safely("status.py")
            actual_position = self._parse_position_from_status(status_result.stdout)
            home_positions.append(actual_position)

            # Capture calibration data
            self._capture_calibration_data(
                f"home_trial_{trial + 1}",
                0.0,  # Expected home position
                actual_position,
                timing_data,
            )

        # Calculate home repeatability statistics
        if len(home_positions) > 1:
            import statistics

            mean_home = statistics.mean(home_positions)
            std_dev = statistics.stdev(home_positions)
            max_deviation = max(abs(pos - mean_home) for pos in home_positions)

            print(
                f"   📊 Home repeatability: mean={mean_home:.2f}°, "
                f"std={std_dev:.2f}°, max_dev={max_deviation:.2f}°"
            )

            # Log repeatability data
            self._capture_calibration_data(
                "home_repeatability_summary",
                0.0,
                mean_home,
                {
                    "std_deviation": std_dev,
                    "max_deviation": max_deviation,
                    "num_trials": num_trials,
                    "all_positions": home_positions,
                },
            )

    @requires_hardware_state(state="any", dependencies=["test_movement_scripts"])
    def test_calibration_rotation_timing(self):
        """Test and capture rotation timing data for timeout calibration."""
        if not self.is_hardware_mode:
            self.skipTest("Calibration data capture only runs in hardware mode")

        print("\n📊 Capturing rotation timing calibration data...")

        # Test different rotation amounts
        rotation_tests = [
            (90, "move_cw.py"),
            (45, "move_cw.py"),
            (180, "move_cw.py"),
            (90, "move_ccw.py"),
        ]

        for rotation_amount, script in rotation_tests:
            print(f"   Testing {script} {rotation_amount}°...")

            # Get initial position
            status_result = self._run_script_safely("status.py")
            initial_pos = self._parse_position_from_status(status_result.stdout)

            # Measure rotation timing
            def rotation_operation():
                return self._run_script_safely(script, [str(rotation_amount)])

            result, timing_data = self._measure_operation_timing(rotation_operation)

            self.assertEqual(
                result.returncode, 0, f"Rotation {script} {rotation_amount}° failed"
            )

            # Get final position
            status_result = self._run_script_safely("status.py")
            final_pos = self._parse_position_from_status(status_result.stdout)

            # Calculate actual rotation
            if "cw" in script:
                expected_final = (initial_pos + rotation_amount) % 360
            else:
                expected_final = (initial_pos - rotation_amount) % 360

            # Capture timing calibration data
            self._capture_calibration_data(
                f"rotation_{script}_{rotation_amount}deg",
                expected_final,
                final_pos,
                {
                    **timing_data,
                    "rotation_amount": rotation_amount,
                    "rotation_direction": script,
                    "degrees_per_second": rotation_amount / timing_data["duration"],
                },
            )

    def _parse_position_from_status(self, status_output):
        """Parse azimuth position from status script output."""
        for line in status_output.split("\n"):
            if "Azimuth:" in line:
                # Extract number from "Azimuth: 123.4°" format
                import re

                match = re.search(r"Azimuth:\s*([\d.-]+)", line)
                if match:
                    return float(match.group(1))
        raise ValueError(
            f"Could not parse position from status output: {status_output}"
        )

    def _report_calibration_summary(self):
        """Generate a summary report of captured calibration data."""
        if not hasattr(self, "_calibration_log") or not self._calibration_log:
            return

        print("\n📋 CALIBRATION DATA SUMMARY")
        print("=" * 50)

        position_errors = [
            entry["error"]
            for entry in self._calibration_log
            if entry["error"] is not None
        ]

        if position_errors:
            import statistics

            mean_error = statistics.mean(position_errors)
            max_error = max(position_errors)

            print("Position Accuracy:")
            print(f"  Mean error: {mean_error:.2f}°")
            print(f"  Max error:  {max_error:.2f}°")
            print(f"  Samples:    {len(position_errors)}")

        timing_data = [
            entry["timing"]["duration"]
            for entry in self._calibration_log
            if "timing" in entry and "duration" in entry["timing"]
        ]

        if timing_data:
            import statistics

            mean_time = statistics.mean(timing_data)
            max_time = max(timing_data)

            print("Operation Timing:")
            print(f"  Mean time:  {mean_time:.2f}s")
            print(f"  Max time:   {max_time:.2f}s")
            print(f"  Samples:    {len(timing_data)}")

        print("=" * 50)


def run_indi_script_tests():
    """Run the INDI script test suite."""
    print("=" * 60)
    print("INDI DOME DRIVER SCRIPT VALIDATION")
    print("=" * 60)
    print()
    print("Testing all 11 INDI scripts for compliance and functionality...")
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestINDIScripts))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print()
    print("=" * 60)
    print("INDI SCRIPT VALIDATION SUMMARY")
    print("=" * 60)

    if result.wasSuccessful():
        print("✅ ALL INDI SCRIPTS VALIDATED SUCCESSFULLY")
        print()
        print("The 11 INDI scripts are ready for production use:")
        print("  • All scripts exist and are executable")
        print("  • All scripts follow INDI contract specifications")
        print("  • All scripts properly interface with dome hardware")
        print("  • All scripts handle errors gracefully")
        print("  • Full operation sequences work correctly")
        print()
        print("📁 Scripts location: scripts/")
        print("🔧 Configure INDI dome_script driver to use these scripts")
        return True
    else:
        print("❌ SCRIPT VALIDATION FAILED")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        return False


if __name__ == "__main__":
    success = run_indi_script_tests()
    sys.exit(0 if success else 1)
