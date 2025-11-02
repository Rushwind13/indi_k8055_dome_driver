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
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

# Add indi_driver/lib directory for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "indi_driver",
        "lib",
    ),
)

from dome import Dome  # noqa: E402


class TestINDIScripts(unittest.TestCase):
    """Test suite for INDI dome script compliance and functionality."""

    def setUp(self):
        """Set up test environment."""
        self.scripts_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "indi_driver", "scripts"
        )
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

    def test_all_scripts_exist(self):
        """Test that all 11 required INDI scripts exist."""
        for script in self.required_scripts:
            script_path = os.path.join(self.scripts_dir, script)
            self.assertTrue(
                os.path.exists(script_path), f"Required INDI script missing: {script}"
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
            ["python3", script_path], capture_output=True, text=True
        )

        # Should succeed (exit code 0)
        self.assertEqual(result.returncode, 0, f"Connect failed: {result.stderr}")
        # Should have no stdout output per INDI contract
        self.assertEqual(result.stdout.strip(), "")

    def test_disconnect_script(self):
        """Test disconnect.py script functionality."""
        script_path = os.path.join(self.scripts_dir, "disconnect.py")

        result = subprocess.run(
            ["python3", script_path], capture_output=True, text=True
        )

        # Should succeed (exit code 0) - disconnect should never fail
        self.assertEqual(result.returncode, 0, f"Disconnect failed: {result.stderr}")
        # Should have no stdout output per INDI contract
        self.assertEqual(result.stdout.strip(), "")

    def test_status_script_output_format(self):
        """Test status.py script output format compliance."""
        script_path = os.path.join(self.scripts_dir, "status.py")

        result = subprocess.run(
            ["python3", script_path], capture_output=True, text=True
        )

        # Should succeed
        self.assertEqual(result.returncode, 0, f"Status failed: {result.stderr}")

        # Parse output format: "parked_status shutter_status azimuth"
        output_parts = result.stdout.strip().split()
        self.assertEqual(
            len(output_parts),
            3,
            f"Status output format wrong: expected 3 values, got {len(output_parts)}",
        )

        # Validate parked status (0 or 1)
        parked_status = int(output_parts[0])
        self.assertIn(parked_status, [0, 1], f"Invalid parked status: {parked_status}")

        # Validate shutter status (0 or 1)
        shutter_status = int(output_parts[1])
        self.assertIn(
            shutter_status, [0, 1], f"Invalid shutter status: {shutter_status}"
        )

        # Validate azimuth (0.0-360.0)
        azimuth = float(output_parts[2])
        self.assertTrue(0.0 <= azimuth <= 360.0, f"Invalid azimuth: {azimuth}")

    def test_shutter_scripts(self):
        """Test shutter open/close scripts."""
        open_script = os.path.join(self.scripts_dir, "open.py")
        close_script = os.path.join(self.scripts_dir, "close.py")

        # Test close script
        result = subprocess.run(
            ["python3", close_script], capture_output=True, text=True
        )
        # May fail if not at home, but should not crash
        self.assertIn(result.returncode, [0, 1])
        self.assertEqual(result.stdout.strip(), "")

        # Test open script
        result = subprocess.run(
            ["python3", open_script], capture_output=True, text=True
        )
        # May fail if not at home, but should not crash
        self.assertIn(result.returncode, [0, 1])
        self.assertEqual(result.stdout.strip(), "")

    def test_park_script(self):
        """Test park.py script functionality."""
        script_path = os.path.join(self.scripts_dir, "park.py")

        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=30,  # Allow time for park sequence
        )

        # Should succeed
        self.assertEqual(result.returncode, 0, f"Park failed: {result.stderr}")
        self.assertEqual(result.stdout.strip(), "")

    def test_unpark_script(self):
        """Test unpark.py script functionality."""
        script_path = os.path.join(self.scripts_dir, "unpark.py")

        result = subprocess.run(
            ["python3", script_path],
            capture_output=True,
            text=True,
            timeout=30,  # Allow time for unpark sequence
        )

        # Should succeed
        self.assertEqual(result.returncode, 0, f"Unpark failed: {result.stderr}")
        self.assertEqual(result.stdout.strip(), "")

    def test_goto_script(self):
        """Test goto.py script functionality."""
        script_path = os.path.join(self.scripts_dir, "goto.py")

        # Test with valid azimuth
        result = subprocess.run(
            ["python3", script_path, "180.0"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        self.assertEqual(result.returncode, 0, f"Goto 180.0 failed: {result.stderr}")
        self.assertEqual(result.stdout.strip(), "")

        # Test with invalid azimuth (should fail)
        result = subprocess.run(
            ["python3", script_path, "400.0"], capture_output=True, text=True
        )

        self.assertEqual(result.returncode, 1, "Goto with invalid azimuth should fail")

        # Test with no arguments (should fail)
        result = subprocess.run(
            ["python3", script_path], capture_output=True, text=True
        )

        self.assertEqual(result.returncode, 1, "Goto with no arguments should fail")

    def test_movement_scripts(self):
        """Test move_cw.py and move_ccw.py scripts."""
        cw_script = os.path.join(self.scripts_dir, "move_cw.py")
        ccw_script = os.path.join(self.scripts_dir, "move_ccw.py")
        abort_script = os.path.join(self.scripts_dir, "abort.py")

        # Test CW movement
        result = subprocess.run(["python3", cw_script], capture_output=True, text=True)

        self.assertEqual(result.returncode, 0, f"Move CW failed: {result.stderr}")
        self.assertEqual(result.stdout.strip(), "")

        # Stop movement
        subprocess.run(["python3", abort_script], capture_output=True)

        # Test CCW movement
        result = subprocess.run(["python3", ccw_script], capture_output=True, text=True)

        self.assertEqual(result.returncode, 0, f"Move CCW failed: {result.stderr}")
        self.assertEqual(result.stdout.strip(), "")

        # Stop movement
        subprocess.run(["python3", abort_script], capture_output=True)

    def test_abort_script(self):
        """Test abort.py script functionality."""
        script_path = os.path.join(self.scripts_dir, "abort.py")

        result = subprocess.run(
            ["python3", script_path], capture_output=True, text=True
        )

        # Abort should never fail (exit code 0)
        self.assertEqual(result.returncode, 0, f"Abort failed: {result.stderr}")
        self.assertEqual(result.stdout.strip(), "")

    def test_script_error_handling(self):
        """Test that scripts handle errors gracefully."""
        # Test all scripts can handle being run when dome is in various states
        scripts_to_test = [
            "connect.py",
            "disconnect.py",
            "status.py",
            "abort.py",  # These should always work
        ]

        for script in scripts_to_test:
            script_path = os.path.join(self.scripts_dir, script)

            with self.subTest(script=script):
                result = subprocess.run(
                    ["python3", script_path], capture_output=True, text=True, timeout=10
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
                result = subprocess.run(
                    ["python3", script_path], capture_output=True, text=True, timeout=30
                )

                # Should return 0 or 1 only (INDI contract)
                self.assertIn(
                    result.returncode,
                    [0, 1],
                    f"Script {script} returned invalid exit code: {result.returncode}",
                )

                # Scripts should not output to stdout except status.py
                if script != "status.py":
                    self.assertEqual(
                        result.stdout.strip(),
                        "",
                        f"Script {script} should not output to stdout",
                    )


class TestINDIScriptIntegration(unittest.TestCase):
    """Integration tests for INDI scripts working together."""

    def setUp(self):
        """Set up test environment."""
        self.scripts_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "indi_driver", "scripts"
        )

    def test_full_operation_sequence(self):
        """Test a complete dome operation sequence using INDI scripts."""

        # 1. Connect
        result = subprocess.run(
            ["python3", os.path.join(self.scripts_dir, "connect.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, "Connect failed")

        # 2. Get initial status
        result = subprocess.run(
            ["python3", os.path.join(self.scripts_dir, "status.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, "Status check failed")

        # 3. Park dome
        result = subprocess.run(
            ["python3", os.path.join(self.scripts_dir, "park.py")],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, "Park failed")

        # 4. Verify parked status
        result = subprocess.run(
            ["python3", os.path.join(self.scripts_dir, "status.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, "Status after park failed")
        status_parts = result.stdout.strip().split()
        parked_status = int(status_parts[0])
        self.assertEqual(parked_status, 1, "Dome should be parked")

        # 5. Test goto operation
        result = subprocess.run(
            ["python3", os.path.join(self.scripts_dir, "goto.py"), "90.0"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, "Goto failed")

        # 6. Test abort
        result = subprocess.run(
            ["python3", os.path.join(self.scripts_dir, "abort.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, "Abort failed")

        # 7. Disconnect
        result = subprocess.run(
            ["python3", os.path.join(self.scripts_dir, "disconnect.py")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, "Disconnect failed")


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
    suite.addTests(loader.loadTestsFromTestCase(TestINDIScriptIntegration))

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
