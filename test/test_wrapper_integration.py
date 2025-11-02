#!/usr/bin/env python3
"""
Integration test for the updated pyk8055_wrapper.

This test verifies that:
1. The old pyk8055.py has been removed
2. The new wrapper uses libk8055 naming conventions
3. The wrapper is compatible with dome.py
4. Mock functionality works properly
5. The wrapper can run standalone
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import dome  # noqa: E402
import pyk8055_wrapper  # noqa: E402


def test_old_pyk8055_removed():
    """Test that the old pyk8055.py file has been removed."""
    print("🔹 Testing that old pyk8055.py has been removed...")
    old_file_path = os.path.join(os.path.dirname(__file__), "..", "pyk8055.py")
    assert not os.path.exists(old_file_path), "Old pyk8055.py should be deleted"
    print("✅ Old pyk8055.py has been removed")


def test_libk8055_naming_conventions():
    """Test that wrapper uses libk8055 naming conventions."""
    print("\n🔹 Testing libk8055 naming conventions...")

    # Test k8055 class exists
    k8055_device = pyk8055_wrapper.k8055(BoardAddress=0, debug=True, mock=True)

    # Test libk8055 method names exist
    assert hasattr(
        k8055_device, "SetDigitalChannel"
    ), "Should have SetDigitalChannel method"
    assert hasattr(
        k8055_device, "ClearDigitalChannel"
    ), "Should have ClearDigitalChannel method"
    assert hasattr(
        k8055_device, "ReadDigitalChannel"
    ), "Should have ReadDigitalChannel method"
    assert hasattr(
        k8055_device, "ReadAnalogChannel"
    ), "Should have ReadAnalogChannel method"
    assert hasattr(k8055_device, "ReadCounter"), "Should have ReadCounter method"
    assert hasattr(k8055_device, "ResetCounter"), "Should have ResetCounter method"
    assert hasattr(
        k8055_device, "SetCounterDebounceTime"
    ), "Should have SetCounterDebounceTime method"
    assert hasattr(k8055_device, "OpenDevice"), "Should have OpenDevice method"
    assert hasattr(k8055_device, "CloseDevice"), "Should have CloseDevice method"
    assert hasattr(k8055_device, "IsOpen"), "Should have IsOpen method"
    assert hasattr(k8055_device, "DeviceAddress"), "Should have DeviceAddress method"

    print("✅ All libk8055 method names present")


def test_compatibility_wrapper():
    """Test that the compatibility wrapper maintains old interface."""
    print("\n🔹 Testing compatibility wrapper...")

    # Test device class exists with old interface
    device = pyk8055_wrapper.device(port=0, mock=True)

    # Test old method names exist
    assert hasattr(device, "digital_on"), "Should have digital_on method"
    assert hasattr(device, "digital_off"), "Should have digital_off method"
    assert hasattr(device, "digital_in"), "Should have digital_in method"
    assert hasattr(device, "analog_in"), "Should have analog_in method"
    assert hasattr(device, "counter_read"), "Should have counter_read method"
    assert hasattr(device, "counter_reset"), "Should have counter_reset method"
    assert hasattr(
        device, "counter_set_debounce"
    ), "Should have counter_set_debounce method"

    print("✅ Compatibility wrapper methods present")


def test_mock_functionality():
    """Test that mock functionality works properly."""
    print("\n🔹 Testing mock functionality...")

    # Test libk8055-style interface
    k8055_device = pyk8055_wrapper.k8055(BoardAddress=1, debug=False, mock=True)

    # Test device is open
    assert k8055_device.IsOpen(), "Device should be open in mock mode"
    assert k8055_device.DeviceAddress() == 1, "Device address should be 1"

    # Test digital operations
    result = k8055_device.SetDigitalChannel(1)
    assert result == 0, "SetDigitalChannel should return 0 on success"

    result = k8055_device.ClearDigitalChannel(1)
    assert result == 0, "ClearDigitalChannel should return 0 on success"

    # Test reading digital input (home switch simulation)
    home_value = k8055_device.ReadDigitalChannel(3)
    assert home_value in [0, 1], "ReadDigitalChannel should return 0 or 1"

    # Test analog operations
    analog_value = k8055_device.ReadAnalogChannel(1)
    assert 0 <= analog_value <= 255, "Analog value should be 0-255"

    # Test counter operations
    k8055_device.ResetCounter(1)
    counter_value = k8055_device.ReadCounter(1)
    assert counter_value >= 0, "Counter value should be non-negative"

    # Test debounce setting
    result = k8055_device.SetCounterDebounceTime(1, 100)
    assert result == 0, "SetCounterDebounceTime should return 0 on success"

    print("✅ Mock functionality working correctly")


def test_dome_integration():
    """Test that dome.py works with the new wrapper."""
    print("\n🔹 Testing dome integration...")

    # Create dome with test configuration
    test_config = {
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
        "testing": {"smoke_test": True, "smoke_test_timeout": 1.0},
    }

    # Test dome creation
    test_dome = dome.Dome(test_config)
    assert test_dome is not None, "Dome should be created successfully"

    # Test basic dome operations
    position = test_dome.get_pos()
    assert position >= 0, "Position should be non-negative"

    # Test digital operations through dome
    test_dome.dome.digital_on(1)
    test_dome.dome.digital_off(1)

    # Test counter operations through dome
    test_dome.counter_reset()
    counters = test_dome.counter_read()
    assert (
        "A" in counters and "B" in counters
    ), "Should return counter dict with A and B"

    # Test shutter operations
    limits = test_dome.get_shutter_limits()
    assert (
        "upper_limit" in limits and "lower_limit" in limits
    ), "Should return limit status"

    print("✅ Dome integration working correctly")


def test_standalone_operation():
    """Test that wrapper can run standalone without dependencies."""
    print("\n🔹 Testing standalone operation...")

    # Test creating multiple devices
    device1 = pyk8055_wrapper.k8055(BoardAddress=0, mock=True)
    device2 = pyk8055_wrapper.k8055(BoardAddress=1, mock=True)

    # Test they have different addresses
    assert (
        device1.DeviceAddress() != device2.DeviceAddress()
    ), "Devices should have different addresses"

    # Test both are functional
    assert device1.IsOpen(), "Device 1 should be open"
    assert device2.IsOpen(), "Device 2 should be open"

    # Test simultaneous operations
    device1.SetDigitalChannel(1)
    device2.SetDigitalChannel(2)

    # Test closing devices
    device1.CloseDevice()
    device2.CloseDevice()

    assert not device1.IsOpen(), "Device 1 should be closed"
    assert not device2.IsOpen(), "Device 2 should be closed"

    print("✅ Standalone operation working correctly")


def main():
    """Run all integration tests."""
    print("=" * 80)
    print("🔭 PYEK8055 WRAPPER INTEGRATION TESTS")
    print("=" * 80)

    try:
        test_old_pyk8055_removed()
        test_libk8055_naming_conventions()
        test_compatibility_wrapper()
        test_mock_functionality()
        test_dome_integration()
        test_standalone_operation()

        print("\n" + "=" * 80)
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print(
            "✅ pyk8055_wrapper successfully updated with libk8055 naming conventions"
        )
        print("✅ Mock functionality works properly")
        print("✅ Compatible with existing dome.py")
        print("✅ Can run standalone")
        print("=" * 80)
        return 0

    except Exception as e:
        print(f"\n❌ INTEGRATION TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
