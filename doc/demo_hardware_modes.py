#!/usr/bin/env python3
"""
Demo: K8055 Wrapper Hardware vs Mock Modes

This demonstrates how the pyk8055_wrapper can operate in:
1. Mock mode (development/testing - no hardware needed)
2. Production mode (real hardware with libk8055 library)

The wrapper automatically detects what's available and adapts accordingly.
"""

import os
import platform
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pyk8055_wrapper  # noqa: E402


def demo_mock_mode():
    """Demonstrate mock mode operation (development/testing)."""
    print("=" * 60)
    print("🔹 MOCK MODE DEMONSTRATION")
    print("=" * 60)
    print("Use case: Development, testing, CI/CD without hardware")
    print()

    # Create device in mock mode
    print("Creating K8055 device in mock mode...")
    device = pyk8055_wrapper.k8055(BoardAddress=0, debug=True, mock=True)
    print(f"Device initialized: {device.IsOpen()}")
    print(f"Device address: {device.DeviceAddress()}")
    print()

    # Demonstrate operations
    print("Testing digital operations...")
    device.SetDigitalChannel(1)  # Turn on dome rotation
    device.SetDigitalChannel(2)  # Set dome direction
    home_status = device.ReadDigitalChannel(3)  # Check home switch
    print(f"Home switch status: {home_status}")
    print()

    print("Testing analog operations...")
    upper_limit = device.ReadAnalogChannel(1)
    lower_limit = device.ReadAnalogChannel(2)
    print(f"Shutter upper limit: {upper_limit}")
    print(f"Shutter lower limit: {lower_limit}")
    print()

    print("Testing counter operations...")
    device.ResetCounter(1)
    # Simulate some encoder movement
    for i in range(3):
        device.SetDigitalChannel(1)  # Rotation on - causes counter increment
        ticks = device.ReadCounter(1)
        print(f"Encoder ticks: {ticks}")

    device.CloseDevice()
    print("✅ Mock mode demonstration complete")


def demo_production_mode():
    """Demonstrate how production mode would work with real hardware."""
    print("\n" + "=" * 60)
    print("⚡ PRODUCTION MODE DEMONSTRATION")
    print("=" * 60)
    print("Use case: Real hardware on Raspberry Pi with libk8055")
    print()

    try:
        # In production, you would set mock=False
        print("Creating K8055 device in production mode...")
        print("(This will fail gracefully since we don't have real hardware)")
        device = pyk8055_wrapper.k8055(BoardAddress=0, debug=True, mock=False)

        # This code would run if real hardware was available
        print("✅ Real hardware detected and connected")
        print(f"Device open: {device.IsOpen()}")

        # All the same operations work with real hardware
        device.SetDigitalChannel(1)
        home_status = device.ReadDigitalChannel(3)
        upper_limit = device.ReadAnalogChannel(1)
        encoder_ticks = device.ReadCounter(1)

        print(f"Real home switch: {home_status}")
        print(f"Real upper limit: {upper_limit}")
        print(f"Real encoder ticks: {encoder_ticks}")

        device.CloseDevice()

    except pyk8055_wrapper.K8055Error as e:
        print(f"❌ Production mode not available: {e}")
        print("This is expected when running without real K8055 hardware")
        print("On Raspberry Pi with libk8055, this would work with real hardware")


def demo_dome_configuration():
    """Show how to configure dome.py for different modes."""
    print("\n" + "=" * 60)
    print("🔧 DOME CONFIGURATION FOR DIFFERENT MODES")
    print("=" * 60)

    # Development configuration (Mock mode)
    print("1. DEVELOPMENT/TESTING CONFIGURATION:")
    print("   File: dome_config.json")

    print("   {")
    print('     "hardware": {')
    print('       "mock_mode": true,          // Enable mock mode')
    print('       "device_port": 0')
    print("     },")
    print('     "testing": {')
    print('       "smoke_test": true,         // Fast testing mode')
    print('       "smoke_test_timeout": 3.0')
    print("     }")
    print("     // ... other settings")
    print("   }")
    print()

    # Production configuration (Real hardware)
    print("2. PRODUCTION CONFIGURATION (Raspberry Pi):")
    print("   File: dome_config.json")
    print("   {")
    print('     "hardware": {')
    print('       "mock_mode": false,         // Use real hardware')
    print('       "device_port": 0            // K8055 device address')
    print("     },")
    print('     "testing": {')
    print('       "smoke_test": false,        // Full operation mode')
    print('       "smoke_test_timeout": 30.0  // Real timeouts')
    print("     },")
    print('     "calibration": {')
    print('       "poll_interval": 0.5,       // Real polling rate')
    print('       "home_position": 225.0,     // Actual home position')
    print('       "ticks_to_degrees": 4.0     // Calibrated ratio')
    print("     }")
    print("     // ... other settings")
    print("   }")
    print()

    # Show how dome.py uses the configuration
    print("3. HOW DOME.PY USES THE CONFIGURATION:")
    print("   In dome.py __init__:")
    print("   ```python")
    print("   mock_mode = self.config['hardware']['mock_mode']")
    print("   device_port = self.config['hardware']['device_port']")
    print("   self.dome = pyk8055_wrapper.device(port=device_port, mock=mock_mode)")
    print("   ```")
    print()
    print("   The wrapper automatically:")
    print("   • Uses mock simulation when mock_mode=True")
    print("   • Attempts real hardware connection when mock_mode=False")
    print("   • Provides identical interface in both modes")


def demo_environment_detection():
    """Show how to automatically detect the environment."""
    print("\n" + "=" * 60)
    print("🤖 AUTOMATIC ENVIRONMENT DETECTION")
    print("=" * 60)

    def detect_hardware_environment():
        """Detect if we're on a system with K8055 hardware capabilities."""
        # Check if we're on Raspberry Pi
        is_raspberry_pi = False
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()
                is_raspberry_pi = "Raspberry Pi" in cpuinfo
        except Exception:
            # File not found or permission error
            is_raspberry_pi = False

        # Check if libk8055 is available
        has_libk8055 = False
        try:
            # This would try to import or detect the actual libk8055 library
            # For demo purposes, we'll just check platform
            has_libk8055 = platform.system() == "Linux" and is_raspberry_pi
        except Exception:
            # Import or detection failed
            has_libk8055 = False

        # Check if we're in a development environment
        is_development = platform.system() == "Darwin"  # macOS

        return {
            "platform": platform.system(),
            "is_raspberry_pi": is_raspberry_pi,
            "has_libk8055": has_libk8055,
            "is_development": is_development,
            "recommended_mock_mode": not has_libk8055,
        }

    env_info = detect_hardware_environment()

    print("Environment detection results:")
    for key, value in env_info.items():
        print(f"  {key}: {value}")

    print()
    print("Recommended configuration:")
    if env_info["recommended_mock_mode"]:
        print("  • Use mock_mode: true")
        print("  • Safe for development/testing")
        print("  • No hardware required")
    else:
        print("  • Use mock_mode: false")
        print("  • Real hardware operation")
        print("  • Production environment detected")

    print()
    print("Auto-configuration code:")
    print("```python")
    print("# In config.py or dome.py")
    print("def get_default_mock_mode():")
    print("    import platform")
    print("    # Default to mock mode on macOS (development)")
    print("    # Default to real mode on Linux (production)")
    print("    return platform.system() != 'Linux'")
    print("")
    print("# Use in configuration")
    print("config['hardware']['mock_mode'] = config.get('hardware', {}).get(")
    print("    'mock_mode', get_default_mock_mode())")
    print("```")


def demo_error_handling():
    """Demonstrate error handling in different modes."""
    print("\n" + "=" * 60)
    print("⚠️  ERROR HANDLING DEMONSTRATION")
    print("=" * 60)

    print("1. MOCK MODE ERROR HANDLING:")
    try:
        device = pyk8055_wrapper.k8055(BoardAddress=0, mock=True)

        # Test invalid parameters
        result = device.SetDigitalChannel(99)  # Invalid channel
        print(f"Invalid channel result: {result}")  # Should return -1

        result = device.ReadAnalogChannel(99)  # Invalid channel
        print(f"Invalid analog channel: {result}")  # Should return -1

        # Mock mode always succeeds for valid operations
        device.CloseDevice()
        print("✅ Mock mode handles errors gracefully")

    except Exception as e:
        print(f"Mock mode error: {e}")

    print()
    print("2. PRODUCTION MODE ERROR HANDLING:")
    try:
        # This will fail since we don't have real hardware
        device = pyk8055_wrapper.k8055(BoardAddress=0, mock=False)
        print("Hardware connected successfully")

    except pyk8055_wrapper.K8055Error as e:
        print(f"✅ Hardware error handled: {e}")
        print("Application can fall back to mock mode or exit gracefully")

    print()
    print("3. DOME.PY ERROR HANDLING STRATEGY:")
    print("```python")
    print("# In dome.py __init__")
    print("try:")
    print("    self.dome = pyk8055_wrapper.device(port=device_port, mock=False)")
    print("    print('Hardware mode: Connected to real K8055')")
    print("except pyk8055_wrapper.K8055Error:")
    print("    print('Hardware not available, falling back to mock mode')")
    print("    self.dome = pyk8055_wrapper.device(port=device_port, mock=True)")
    print("```")


def main():
    """Run all demonstrations."""
    print("🔭 K8055 WRAPPER: MOCK vs PRODUCTION MODE DEMO")
    print("This shows how to use the wrapper in different environments")

    demo_mock_mode()
    demo_production_mode()
    demo_dome_configuration()
    demo_environment_detection()
    demo_error_handling()

    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    print("✅ Mock Mode (Development):")
    print("   • Set mock_mode: true in config")
    print("   • No hardware required")
    print("   • Safe for testing on any platform")
    print("   • Identical interface to real hardware")
    print()
    print("✅ Production Mode (Raspberry Pi):")
    print("   • Set mock_mode: false in config")
    print("   • Requires K8055 hardware and libk8055")
    print("   • Real dome operations")
    print("   • Same code, real results")
    print()
    print("✅ Configuration Strategy:")
    print("   • Use config files for environment-specific settings")
    print("   • Automatic environment detection possible")
    print("   • Graceful fallback from hardware to mock mode")
    print("   • Same API in all modes")


if __name__ == "__main__":
    main()
