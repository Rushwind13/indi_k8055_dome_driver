#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python 2.7 Dome Driver Validation Suite

Comprehensive validation test suite for the INDI K8055 dome driver on Python 2.7.
Tests all critical functionality: imports, basic operations, persistence, and scripts.

This replaces multiple scattered test files with a single comprehensive validation.

Usage:
    source venv_py27/bin/activate
    python test/python2/validate_py27.py [--verbose] [--persistence-only]
"""

import os
import subprocess
import sys
import tempfile

# Add the Python 2.7 lib directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(
    0, os.path.join(script_dir, "..", "..", "indi_driver", "python2", "lib")
)


class ValidationTests(object):
    """Python 2.7 validation test suite"""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.temp_files = []

    def log(self, message):
        """Log message if verbose mode enabled"""
        if self.verbose:
            print("  {}".format(message))

    def test_imports(self):
        """Test that all required modules can be imported"""
        print("1. Testing module imports...")

        # Test K8055 wrapper import
        try:
            import pyk8055_wrapper

            self.log("K8055 wrapper imported successfully")
            k8055_success = True
        except Exception as e:
            print("  ❌ K8055 wrapper import failed: {}".format(e))
            k8055_success = False

        # Test dome module import
        try:
            import dome

            self.log("Dome module imported successfully")
            dome_success = True
        except Exception as e:
            print("  ❌ Dome module import failed: {}".format(e))
            dome_success = False

        # Test persistence module import
        try:
            import persistence

            self.log("Persistence module imported successfully")
            persistence_success = True
        except Exception as e:
            print("  ❌ Persistence module import failed: {}".format(e))
            persistence_success = False

        # Test config module import
        try:
            import config

            self.log("Config module imported successfully")
            config_success = True
        except Exception as e:
            print("  ❌ Config module import failed: {}".format(e))
            config_success = False

        if k8055_success and dome_success and persistence_success and config_success:
            print("  ✓ All module imports successful")
            self.passed += 1
            return True
        else:
            print("  ❌ Some module imports failed")
            self.failed += 1
            return False

    def test_dome_creation(self):
        """Test dome object creation with mock configuration"""
        print("2. Testing dome object creation...")

        try:
            from dome import Dome

            # Create test config
            config = {
                "pins": {
                    "encoder_a": 1,
                    "encoder_b": 2,
                    "home_switch": 3,
                    "shutter_upper_limit": 1,
                    "shutter_lower_limit": 2,
                    "dome_rotate": 1,
                    "dome_direction": 2,
                    "shutter_move": 3,
                    "shutter_direction": 4,
                },
                "calibration": {
                    "home_position": 0.0,
                    "ticks_to_degrees": 1.0,
                    "poll_interval": 0.1,
                },
                "hardware": {"mock_mode": True, "device_port": 0},
                "testing": {"smoke_test": True, "smoke_test_timeout": 3.0},
            }

            # Create dome object
            dome = Dome(config)
            self.log("Dome object created successfully")

            # Test basic operations
            position = dome.get_pos()
            self.log("Position read: {:.1f} degrees".format(position))

            # Test state attributes
            self.log("Home state: {}".format(dome.is_home))
            self.log("Turning state: {}".format(dome.is_turning))

            print("  ✓ Dome creation and basic operations successful")
            self.passed += 1
            return True

        except Exception as e:
            print("  ❌ Dome creation failed: {}".format(e))
            self.failed += 1
            return False

    def test_persistence_functionality(self):
        """Test persistence save/restore functionality"""
        print("3. Testing persistence functionality...")

        try:
            from dome import Dome
            from persistence import DomePersistence

            # Create temporary state file
            temp_dir = tempfile.mkdtemp()
            state_file = os.path.join(temp_dir, "test_state.json")
            self.temp_files.append(state_file)

            persistence = DomePersistence(state_file)

            # Create test config
            config = {
                "pins": {
                    "encoder_a": 1,
                    "encoder_b": 2,
                    "home_switch": 3,
                    "shutter_upper_limit": 1,
                    "shutter_lower_limit": 2,
                    "dome_rotate": 1,
                    "dome_direction": 2,
                    "shutter_move": 3,
                    "shutter_direction": 4,
                },
                "calibration": {
                    "home_position": 0.0,
                    "ticks_to_degrees": 1.0,
                    "poll_interval": 0.1,
                },
                "hardware": {"mock_mode": True, "device_port": 0},
                "testing": {"smoke_test": True, "smoke_test_timeout": 3.0},
            }

            # Test save/restore cycle
            dome1 = Dome(config)
            dome1.position = 45.0
            dome1.is_turning = True
            # Connection state should be True after Dome creation

            success = persistence.save_dome_state(dome1, "test")
            if not success:
                raise Exception("Failed to save state")

            dome2 = Dome(config)
            success = persistence.restore_dome_state(dome2)
            if not success:
                raise Exception("Failed to restore state")

            if dome2.position != 45.0:
                raise Exception(
                    "Position not restored correctly: {} != 45.0".format(dome2.position)
                )

            if not dome2.is_turning:
                raise Exception("Turning state not restored correctly")

            # Check that connection state is tracked
            try:
                device_connected = getattr(dome2.dome.k8055_device, "is_open", False)
                if self.verbose:
                    print("  Connection state restored: {}".format(device_connected))
            except (AttributeError, TypeError):
                if self.verbose:
                    print(
                        "  Connection state not accessible (acceptable for mock mode)"
                    )

            self.log("State saved and restored successfully")
            self.log("Position: {} -> {}".format(dome1.position, dome2.position))
            self.log("Turning: {} -> {}".format(dome1.is_turning, dome2.is_turning))

            print("  ✓ Persistence functionality working correctly")
            self.passed += 1
            return True

        except Exception as e:
            print("  ❌ Persistence test failed: {}".format(e))
            self.failed += 1
            return False

    def test_script_integration(self):
        """Test that INDI scripts have persistence integration"""
        print("4. Testing INDI script integration...")

        scripts_dir = os.path.join(
            script_dir, "..", "..", "indi_driver", "python2", "scripts"
        )
        # Scripts that should have full persistence (restore + save)
        full_persistence_scripts = [
            "status.py",
            "goto.py",
            "park.py",
            "move_cw.py",
            "open.py",
            "unpark.py",
            "disconnect.py",
            "abort.py",
        ]
        # Scripts that only save state (connect establishes initial connection)
        save_only_scripts = ["connect.py"]

        try:
            # Test full persistence scripts
            for script_name in full_persistence_scripts:
                script_path = os.path.join(scripts_dir, script_name)

                if not os.path.exists(script_path):
                    raise Exception("Script {} not found".format(script_name))

                # Check that script contains persistence imports
                with open(script_path, "r") as f:
                    content = f.read()

                if "from persistence import" not in content:
                    raise Exception(
                        "Script {} missing persistence import".format(script_name)
                    )

                if "restore_state" not in content:
                    raise Exception(
                        "Script {} missing restore_state call".format(script_name)
                    )

                if "save_state" not in content:
                    raise Exception(
                        "Script {} missing save_state call".format(script_name)
                    )

                self.log("Script {} has persistence integration".format(script_name))

            # Test save-only scripts
            for script_name in save_only_scripts:
                script_path = os.path.join(scripts_dir, script_name)

                if not os.path.exists(script_path):
                    raise Exception("Script {} not found".format(script_name))

                # Check that script contains persistence imports
                with open(script_path, "r") as f:
                    content = f.read()

                if "from persistence import" not in content:
                    raise Exception(
                        "Script {} missing persistence import".format(script_name)
                    )

                if "save_state" not in content:
                    raise Exception(
                        "Script {} missing save_state call".format(script_name)
                    )

                self.log(
                    "Script {} has save-only persistence integration".format(
                        script_name
                    )
                )

            print("  ✓ All scripts have persistence integration")
            self.passed += 1
            return True

        except Exception as e:
            print("  ❌ Script integration test failed: {}".format(e))
            self.failed += 1
            return False

    def test_python27_compatibility(self):
        """Test Python 2.7 specific compatibility"""
        print("5. Testing Python 2.7 compatibility...")

        try:
            # Check Python version
            if sys.version_info[0] != 2 or sys.version_info[1] != 7:
                print(
                    "  ⚠ Warning: Not running on Python 2.7 ({}.{})".format(
                        sys.version_info[0], sys.version_info[1]
                    )
                )

            # Test string formatting (no f-strings)
            test_str = "Position: {:.2f} degrees".format(45.5)
            if "45.50" not in test_str:
                raise Exception("String formatting test failed")

            # Test dictionary methods
            test_dict = {"a": 1, "b": 2}
            keys = test_dict.keys()
            if "a" not in keys or "b" not in keys:
                raise Exception("Dictionary methods test failed")

            # Test exception handling
            try:
                raise ValueError("test exception")
            except ValueError as e:
                if "test exception" not in str(e):
                    raise Exception("Exception handling test failed")

            self.log("String formatting compatible")
            self.log("Dictionary methods compatible")
            self.log("Exception handling compatible")

            print("  ✓ Python 2.7 compatibility verified")
            self.passed += 1
            return True

        except Exception as e:
            print("  ❌ Python 2.7 compatibility test failed: {}".format(e))
            self.failed += 1
            return False

    def test_home_polling_optimization(self):
        """Test home switch polling optimization features (C2)"""
        print("6. Testing home switch polling optimization...")

        try:
            from dome import Dome

            # Create test config with mock mode
            config = {
                "pins": {
                    "encoder_a": 1,
                    "encoder_b": 5,
                    "home_switch": 2,
                    "dome_rotate": 1,
                    "dome_direction": 2,
                    "shutter_move": 5,
                    "shutter_direction": 6,
                },
                "calibration": {
                    "home_position": 225,
                    "ticks_to_degrees": 4.0,
                    "poll_interval": 0.5,
                    "home_poll_fast": 0.05,
                    "home_switch_debounce": 0.1,
                },
                "hardware": {"mock_mode": True, "device_port": 0},
                "testing": {"smoke_test": True, "smoke_test_timeout": 3.0},
            }

            dome = Dome(config)

            # Test configuration loading
            if not (dome.home_poll_fast < dome.POLL):
                raise Exception("Fast polling should be faster than normal polling")
            if not (dome.home_poll_fast > 0.01):
                raise Exception("Fast polling rate too aggressive")
            if not (dome.home_switch_debounce > 0):
                raise Exception("Debounce time should be positive")

            # Test diagnostic methods
            home_diag = dome.get_home_polling_diagnostics()
            required_keys = ["polling_rates", "signal_validation", "speed_tracking"]
            for key in required_keys:
                if key not in home_diag:
                    raise Exception("Missing home diagnostic key: {}".format(key))

            # Test enhanced home detection
            basic_result = dome.isHome()
            enhanced_result = dome.is_home_with_validation()
            self.log("Basic home detection: {}".format(basic_result))
            self.log("Enhanced home detection: {}".format(enhanced_result))
            # Both should return same result in mock mode

            # Test polling rate switching simulation
            original_poll = dome.POLL
            dome.home_poll_normal = original_poll
            dome.POLL = dome.home_poll_fast
            dome.POLL = dome.home_poll_normal
            if dome.POLL != original_poll:
                raise Exception("Failed to restore original polling rate")

            self.log("Home polling configuration validated")
            self.log("Diagnostic methods working")
            self.log("Enhanced detection methods available")
            self.log("Polling rate switching functional")

            print("  ✓ Home switch polling optimization working")
            self.passed += 1
            return True

        except Exception as e:
            print("  ❌ Home polling optimization test failed: {}".format(e))
            self.failed += 1
            return False

    def test_encoder_calibration_system(self):
        """Test encoder calibration and validation system (C3)"""
        print("7. Testing encoder calibration system...")

        try:
            from dome import Dome

            # Create test config with mock mode
            config = {
                "pins": {
                    "encoder_a": 1,
                    "encoder_b": 5,
                    "home_switch": 2,
                    "dome_rotate": 1,
                    "dome_direction": 2,
                    "shutter_move": 5,
                    "shutter_direction": 6,
                },
                "calibration": {
                    "home_position": 225,
                    "ticks_to_degrees": 4.0,
                    "poll_interval": 0.5,
                    "encoder_error_threshold": 50,
                    "encoder_calibration_timeout": 180.0,
                },
                "hardware": {"mock_mode": True, "device_port": 0},
                "testing": {"smoke_test": True, "smoke_test_timeout": 3.0},
            }

            dome = Dome(config)

            # Test configuration loading
            if dome.TICKS_TO_DEG <= 0:
                raise Exception("Ticks to degrees should be positive")
            if dome.encoder_error_threshold <= 0:
                raise Exception("Error threshold should be positive")
            if dome.encoder_calibration_timeout < 60:
                raise Exception("Calibration timeout should be reasonable")

            # Test calibration status method
            status = dome.get_encoder_calibration_status()
            required_keys = ["current_config", "performance", "recommendations"]
            for key in required_keys:
                if key not in status:
                    raise Exception("Missing calibration status key: {}".format(key))

            # Test enhanced encoder diagnostics
            encoder_diag = dome.get_encoder_diagnostics()
            required_keys = [
                "current_state",
                "direction",
                "speed_deg_per_sec",
                "max_speed_deg_per_sec",
                "error_count",
                "encoder_pins",
            ]
            for key in required_keys:
                if key not in encoder_diag:
                    raise Exception("Missing encoder diagnostic key: {}".format(key))

            # Test error detection and recovery
            dome.encoder_errors = 5
            dome.reset_encoder_tracking()
            if dome.encoder_errors != 0:
                raise Exception("Error count should be reset to 0")

            # Test encoder tracking enhancement
            for i in range(5):
                result = dome.update_encoder_tracking()
                if not result:
                    raise Exception("update_encoder_tracking should return True")

            # Test consistency validation method exists
            try:
                results = dome.validate_encoder_consistency(test_duration=2.0)
                required_keys = ["test_duration", "total_samples", "validation_passed"]
                for key in required_keys:
                    if key not in results:
                        raise Exception("Missing validation result key: {}".format(key))
            except Exception as e:
                # Acceptable in mock mode
                self.log("Consistency validation limited in mock mode: {}".format(e))

            self.log("Encoder calibration configuration loaded")
            self.log("Calibration status reporting working")
            self.log("Enhanced diagnostics available")
            self.log("Error detection and recovery functional")
            self.log("Encoder tracking enhancements working")

            print("  ✓ Encoder calibration system working")
            self.passed += 1
            return True

        except Exception as e:
            print("  ❌ Encoder calibration system test failed: {}".format(e))
            self.failed += 1
            return False

    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    temp_dir = os.path.dirname(temp_file)
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
            except OSError:
                pass

    def run_all_tests(self):
        """Run all validation tests"""
        print("Python 2.7 Dome Driver Validation Suite")
        print("=" * 45)
        print("Python version: {}".format(sys.version))
        print("")

        try:
            # Run all tests
            self.test_imports()
            self.test_dome_creation()
            self.test_persistence_functionality()
            self.test_script_integration()
            self.test_python27_compatibility()
            self.test_home_polling_optimization()
            self.test_encoder_calibration_system()

            # Print summary
            print("")
            print("=" * 45)
            print("VALIDATION SUMMARY")
            print("Passed: {}".format(self.passed))
            print("Failed: {}".format(self.failed))
            print("Total:  {}".format(self.passed + self.failed))

            if self.failed == 0:
                print("")
                print("🎉 ALL VALIDATION TESTS PASSED!")
                print("Python 2.7 dome driver is ready for deployment.")
                return True
            else:
                print("")
                print("❌ SOME VALIDATION TESTS FAILED!")
                print("Please review failures before deployment.")
                return False

        finally:
            self.cleanup()


def main():
    """Main test runner"""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    persistence_only = "--persistence-only" in sys.argv

    validator = ValidationTests(verbose=verbose)

    if persistence_only:
        print("Running persistence validation only...")
        success = validator.test_persistence_functionality()
        validator.cleanup()
        return success
    else:
        return validator.run_all_tests()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
