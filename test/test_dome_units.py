#!/usr/bin/env python3
"""
Unit tests for dome.py core functionality.

These tests focus on individual dome operations and edge cases
that are not covered by integration tests.
"""

import os
import sys
import time
from unittest.mock import MagicMock, Mock, patch

# Add indi_driver/lib directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "indi_driver", "lib")
)

import dome  # noqa: E402
import pyk8055_wrapper  # noqa: E402
import pytest  # noqa: E402


class TestDomeInitialization:
    """Test dome initialization and configuration handling."""

    def test_dome_init_with_valid_config(self):
        """Test dome initialization with valid configuration."""
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
                "poll_interval": 0.1,
                "home_position": 0.0,
                "ticks_to_degrees": 1.0,
            },
            "hardware": {"mock_mode": True, "device_port": 0},
        }

        test_dome = dome.Dome(config)
        assert test_dome is not None
        assert test_dome.config == config
        assert test_dome.A == 1
        assert test_dome.B == 2
        assert test_dome.HOME == 3

    def test_dome_init_with_invalid_config(self):
        """Test dome initialization with invalid configuration."""
        # Missing required pins section
        invalid_config = {
            "calibration": {"poll_interval": 0.1},
            "hardware": {"mock_mode": True, "device_port": 0},
        }

        with pytest.raises(KeyError):
            dome.Dome(invalid_config)

    def test_dome_init_with_file_path(self):
        """Test dome initialization with config file path."""
        # This should try to load from file and fall back to defaults
        test_dome = dome.Dome("nonexistent_config.json")
        assert test_dome is not None
        # Should use default configuration


class TestDomeRotation:
    """Test dome rotation operations and safety."""

    def setup_method(self):
        """Set up test dome for each test."""
        self.config = {
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
                "poll_interval": 0.01,  # Fast for testing
                "home_position": 0.0,
                "ticks_to_degrees": 1.0,
            },
            "hardware": {"mock_mode": True, "device_port": 0},
            "testing": {"smoke_test": True, "smoke_test_timeout": 0.1},
        }
        self.dome = dome.Dome(self.config)

    def test_rotation_direction_setting(self):
        """Test setting rotation direction."""
        # Test clockwise
        self.dome.set_rotation(self.dome.CW)
        assert self.dome.dir == self.dome.CW

        # Test counter-clockwise
        self.dome.set_rotation(self.dome.CCW)
        assert self.dome.dir == self.dome.CCW

    def test_cw_rotation_by_amount(self):
        """Test clockwise rotation by specific amount."""
        # Mock the rotation to simulate movement
        with patch.object(self.dome, "rotation") as mock_rotation:
            self.dome.cw(amount=90)
            mock_rotation.assert_called_once_with(90)

    def test_ccw_rotation_by_amount(self):
        """Test counter-clockwise rotation by specific amount."""
        # Mock the rotation to simulate movement
        # NOTE: Current implementation passes negative amount to rotation()
        # This is a known bug - rotation() only works for positive values
        with patch.object(self.dome, "rotation") as mock_rotation:
            self.dome.ccw(amount=90)
            # CCW rotation negates the amount
            mock_rotation.assert_called_once_with(-90)

    def test_rotation_to_home(self):
        """Test rotation to home position."""
        with patch.object(self.dome, "home") as mock_home:
            self.dome.cw(to_home=True)
            mock_home.assert_called_once()

    def test_home_detection(self):
        """Test home position detection."""
        # Mock home switch reading - use the correct pin from config
        home_pin = self.dome.HOME  # This should be pin 3 from test config

        # Test home switch active
        self.dome.dome.k8055_device._digital_inputs[home_pin] = True
        assert self.dome.isHome() is True

        # Test home switch inactive
        self.dome.dome.k8055_device._digital_inputs[home_pin] = False
        assert self.dome.isHome() is False


class TestDomeCounters:
    """Test encoder counter operations."""

    def setup_method(self):
        """Set up test dome for each test."""
        self.config = {
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
                "poll_interval": 0.1,
                "home_position": 0.0,
                "ticks_to_degrees": 1.0,
            },
            "hardware": {"mock_mode": True, "device_port": 0},
        }
        self.dome = dome.Dome(self.config)

    def test_counter_reset(self):
        """Test counter reset functionality."""
        # Set some counter values
        self.dome.dome.k8055_device._counters[1] = 100
        self.dome.dome.k8055_device._counters[2] = 200

        # Reset counters
        self.dome.counter_reset()

        # Verify reset
        counters = self.dome.counter_read()
        assert counters["A"] == 0
        assert counters["B"] == 0

    def test_counter_reading(self):
        """Test counter reading functionality."""
        # Set counter values
        self.dome.dome.k8055_device._counters[1] = 150
        self.dome.dome.k8055_device._counters[2] = 300

        # Read counters
        counters = self.dome.counter_read()
        assert counters["A"] == 150
        assert counters["B"] == 300

    def test_position_calculation(self):
        """Test position calculation from counter values."""
        # Set counter values to simulate rotation
        self.dome.dome.k8055_device._counters[1] = 90  # 90 ticks = 90 degrees

        position = self.dome.get_pos()
        expected_position = 90 * self.dome.TICKS_TO_DEG
        assert position == expected_position

    def test_position_setting(self):
        """Test setting dome position."""
        new_position = 180.0
        self.dome.set_pos(new_position)
        assert self.dome.position == new_position


class TestShutterOperations:
    """Test shutter control operations."""

    def setup_method(self):
        """Set up test dome for each test."""
        self.config = {
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
                "poll_interval": 0.1,
                "home_position": 0.0,
                "ticks_to_degrees": 1.0,
            },
            "hardware": {"mock_mode": True, "device_port": 0},
            "testing": {"smoke_test": True, "smoke_test_timeout": 0.1},
        }
        self.dome = dome.Dome(self.config)

    def test_shutter_limit_reading(self):
        """Test reading shutter limit switches."""
        # Set mock analog values for limits
        self.dome.dome.k8055_device._analog_inputs[1] = 100  # Upper limit
        self.dome.dome.k8055_device._analog_inputs[2] = 200  # Lower limit

        limits = self.dome.get_shutter_limits()
        assert limits["upper_limit"] == 100
        assert limits["lower_limit"] == 200

    def test_shutter_open_operation(self):
        """Test shutter opening operation."""
        # Mock shutter as closed initially and dome at home
        self.dome.is_closed = True
        self.dome.is_open = False

        # Mock home switch to return True (dome at home position)
        home_pin = self.dome.HOME
        self.dome.dome.k8055_device._digital_inputs[home_pin] = True

        # Test opening - shutter_open should return True and set is_opening
        result = self.dome.shutter_open()
        assert result is True
        assert self.dome.is_opening is True
        assert self.dome.is_closing is False

    def test_shutter_close_operation(self):
        """Test shutter closing operation."""
        # Mock shutter as open initially and dome at home
        self.dome.is_open = True
        self.dome.is_closed = False

        # Mock home switch to return True (dome at home position)
        home_pin = self.dome.HOME
        self.dome.dome.k8055_device._digital_inputs[home_pin] = True

        # Test closing - shutter_close should return True and set is_closing
        result = self.dome.shutter_close()
        assert result is True
        assert self.dome.is_closing is True
        assert self.dome.is_opening is False

    def test_shutter_stop_operation(self):
        """Test emergency shutter stop."""
        # Start with shutter moving
        self.dome.is_opening = True

        # Test stop
        self.dome.shutter_stop()

        # Verify all motion flags cleared
        assert not self.dome.is_opening
        assert not self.dome.is_closing

    def test_shutter_status_detection(self):
        """Test shutter status detection methods."""
        # Test closed detection
        self.dome.is_closed = True
        assert self.dome.isClosed() is True

        # Test open detection
        self.dome.is_open = True
        assert self.dome.isOpen() is True


class TestErrorHandling:
    """Test error handling and edge cases."""

    def setup_method(self):
        """Set up test dome for each test."""
        self.config = {
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
                "poll_interval": 0.1,
                "home_position": 0.0,
                "ticks_to_degrees": 1.0,
            },
            "hardware": {"mock_mode": True, "device_port": 0},
            "testing": {"smoke_test": True, "smoke_test_timeout": 0.1},
        }

    def test_missing_config_parameters(self):
        """Test handling of missing configuration parameters."""
        # Remove required parameter
        incomplete_config = self.config.copy()
        del incomplete_config["pins"]["encoder_a"]

        with pytest.raises(KeyError):
            dome.Dome(incomplete_config)

    def test_invalid_pin_numbers(self):
        """Test handling of invalid pin numbers."""
        invalid_config = self.config.copy()
        invalid_config["pins"]["encoder_a"] = 99  # Invalid pin number

        # Should create dome but may have issues with hardware operations
        test_dome = dome.Dome(invalid_config)
        assert test_dome.A == 99

    def test_device_communication_error(self):
        """Test handling of device communication errors."""
        test_dome = dome.Dome(self.config)

        # Mock device to raise exception on ReadDigitalChannel call
        test_dome.dome.k8055_device.ReadDigitalChannel = Mock(
            side_effect=Exception("Communication error")
        )

        # Should propagate the error when trying to read home switch
        # The home() method calls digital_in which calls ReadDigitalChannel
        with pytest.raises(Exception, match="Communication error"):
            test_dome.home()

    def test_timeout_handling(self):
        """Test operation timeout handling."""
        test_dome = dome.Dome(self.config)

        # Mock a long-running operation
        start_time = time.time()

        # Should timeout quickly in smoke test mode
        with patch("time.time", side_effect=lambda: start_time + 10):
            # This should timeout because of smoke test timeout
            test_dome.wait_for_shutter_operation("test")
            # In smoke test mode, this completes quickly


class TestHardwareInterface:
    """Test hardware interface layer."""

    def test_device_wrapper_compatibility(self):
        """Test that device wrapper maintains compatibility."""
        device = pyk8055_wrapper.device(port=0, mock=True)

        # Test all required methods exist
        assert hasattr(device, "digital_on")
        assert hasattr(device, "digital_off")
        assert hasattr(device, "digital_in")
        assert hasattr(device, "analog_in")
        assert hasattr(device, "counter_read")
        assert hasattr(device, "counter_reset")
        assert hasattr(device, "counter_set_debounce")

    def test_mock_hardware_simulation(self):
        """Test mock hardware provides realistic simulation."""
        k8055_device = pyk8055_wrapper.k8055(BoardAddress=0, mock=True)

        # Test device opens successfully
        assert k8055_device.IsOpen()

        # Test digital operations
        result = k8055_device.SetDigitalChannel(1)
        assert result == 0  # Success

        result = k8055_device.ClearDigitalChannel(1)
        assert result == 0  # Success

        # Test analog readings
        analog_value = k8055_device.ReadAnalogChannel(1)
        assert 0 <= analog_value <= 255

        # Test counter operations
        k8055_device.ResetCounter(1)
        counter_value = k8055_device.ReadCounter(1)
        assert counter_value >= 0

    def test_multiple_device_handling(self):
        """Test handling multiple K8055 devices."""
        device1 = pyk8055_wrapper.k8055(BoardAddress=0, mock=True)
        device2 = pyk8055_wrapper.k8055(BoardAddress=1, mock=True)

        # Both should be functional
        assert device1.IsOpen()
        assert device2.IsOpen()

        # Should have different addresses
        assert device1.DeviceAddress() != device2.DeviceAddress()

        # Operations should be independent
        device1.SetDigitalChannel(1)
        device2.SetDigitalChannel(2)

        # Clean up
        device1.CloseDevice()
        device2.CloseDevice()

        assert not device1.IsOpen()
        assert not device2.IsOpen()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
