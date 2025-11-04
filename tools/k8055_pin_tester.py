#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
K8055 Pin Configuration and Testing Tool

This script provides granular control and testing of K8055 pins to help diagnose
and fix pin configuration issues with the dome driver.

Features:
- Test individual digital/analog pins
- Validate pin configurations
- Interactive pin testing mode
- Configuration diagnosis
- Pin mapping verification

Usage:
    # Interactive mode - test pins manually
    python k8055_pin_tester.py --interactive

    # Test specific configuration
    python k8055_pin_tester.py --config dome_config.json

    # Test all pins systematically
    python k8055_pin_tester.py --test-all

    # Show pin mappings and help
    python k8055_pin_tester.py --help-pins
"""

import argparse
import json
import os
import sys
import time

# Add Python 2.7 and Python 3 lib paths
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(script_dir, "indi_driver", "lib"))
sys.path.insert(0, os.path.join(script_dir, "indi_driver", "python2", "lib"))

# Python 2/3 compatibility
try:
    input_func = raw_input
except NameError:
    input_func = input


def print_header(title):
    """Print a formatted header."""
    print("=" * 60)
    print(title)
    print("=" * 60)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "-" * 40)
    print(title)
    print("-" * 40)


def test_k8055_import():
    """Test if K8055 wrapper can be imported."""
    print_section("Testing K8055 Import")

    try:
        # Try Python 3 version first
        try:
            import pyk8055_wrapper

            print("✓ Python 3 pyk8055_wrapper imported successfully")
            return pyk8055_wrapper, "python3"
        except ImportError:
            # Fallback to Python 2.7 path
            sys.path.insert(
                0, os.path.join(script_dir, "indi_driver", "python2", "lib")
            )
            import pyk8055_wrapper

            print("✓ Python 2.7 pyk8055_wrapper imported successfully")
            return pyk8055_wrapper, "python2.7"

    except ImportError as e:
        print("❌ Failed to import pyk8055_wrapper: {}".format(e))
        print("\nTroubleshooting:")
        print("1. Make sure you're running from the project root directory")
        print("2. Check that indi_driver/lib/ or indi_driver/python2/lib/ exists")
        print("3. Verify pyk8055_wrapper.py is in the lib directory")
        return None, None


def create_test_device(mock_mode=True, device_port=0):
    """Create a K8055 test device."""
    try:
        pyk8055_wrapper, python_version = test_k8055_import()
        if not pyk8055_wrapper:
            return None

        print(
            "\nCreating K8055 device (mock_mode={}, port={})...".format(
                mock_mode, device_port
            )
        )

        # Try both interface styles
        try:
            # New k8055 class interface
            device = pyk8055_wrapper.k8055(
                BoardAddress=device_port, debug=True, mock=mock_mode
            )
            print("✓ Using k8055 class interface")
            return device
        except AttributeError:
            # Old device wrapper interface
            device = pyk8055_wrapper.device(port=device_port, mock=mock_mode)
            print("✓ Using device wrapper interface")
            return device

    except Exception as e:
        print("❌ Failed to create K8055 device: {}".format(e))
        return None


def test_digital_outputs(device):
    """Test all digital output pins."""
    print_section("Testing Digital Outputs (Pins 1-8)")

    if not device:
        print("❌ No device available for testing")
        return False

    results = {}

    for pin in range(1, 9):
        print("\nTesting digital output pin {}...".format(pin))

        try:
            # Test turning pin ON
            if hasattr(device, "SetDigitalChannel"):
                result_on = device.SetDigitalChannel(pin)
            else:
                result_on = device.digital_on(pin)

            if result_on == 0:
                print("  ✓ Pin {} ON: Success".format(pin))
            else:
                print("  ❌ Pin {} ON: Failed (result: {})".format(pin, result_on))

            time.sleep(0.1)

            # Test turning pin OFF
            if hasattr(device, "ClearDigitalChannel"):
                result_off = device.ClearDigitalChannel(pin)
            else:
                result_off = device.digital_off(pin)

            if result_off == 0:
                print("  ✓ Pin {} OFF: Success".format(pin))
                results[pin] = True
            else:
                print("  ❌ Pin {} OFF: Failed (result: {})".format(pin, result_off))
                results[pin] = False

        except Exception as e:
            print("  ❌ Pin {} ERROR: {}".format(pin, e))
            results[pin] = False

    return results


def test_digital_inputs(device):
    """Test all digital input pins."""
    print_section("Testing Digital Inputs (Pins 1-5)")

    if not device:
        print("❌ No device available for testing")
        return False

    results = {}

    for pin in range(1, 6):
        print("\nTesting digital input pin {}...".format(pin))

        try:
            if hasattr(device, "ReadDigitalChannel"):
                value = device.ReadDigitalChannel(pin)
            else:
                value = device.digital_in(pin)

            if value >= 0:  # 0 or 1 are valid
                print(
                    "  ✓ Pin {} value: {} {}".format(
                        pin, value, "(HIGH)" if value else "(LOW)"
                    )
                )
                results[pin] = True
            else:
                print("  ❌ Pin {} ERROR: Invalid value {}".format(pin, value))
                results[pin] = False

        except Exception as e:
            print("  ❌ Pin {} ERROR: {}".format(pin, e))
            results[pin] = False

    return results


def test_analog_inputs(device):
    """Test analog input channels."""
    print_section("Testing Analog Inputs (Channels 1-2)")

    if not device:
        print("❌ No device available for testing")
        return False

    results = {}

    for channel in range(1, 3):
        print("\nTesting analog input channel {}...".format(channel))

        try:
            if hasattr(device, "ReadAnalogChannel"):
                value = device.ReadAnalogChannel(channel)
            else:
                value = device.analog_in(channel)

            if 0 <= value <= 255:
                print(
                    "  ✓ Channel {} value: {} ({}%)".format(
                        channel, value, round(value / 255.0 * 100, 1)
                    )
                )
                results[channel] = True
            else:
                print(
                    "  ❌ Channel {} ERROR: Value {} out of range (0-255)".format(
                        channel, value
                    )
                )
                results[channel] = False

        except Exception as e:
            print("  ❌ Channel {} ERROR: {}".format(channel, e))
            results[channel] = False

    return results


def test_counters(device):
    """Test counter channels."""
    print_section("Testing Counters (Channels 1-2)")

    if not device:
        print("❌ No device available for testing")
        return False

    results = {}

    for counter in range(1, 3):
        print("\nTesting counter {}...".format(counter))

        try:
            # Reset counter
            if hasattr(device, "ResetCounter"):
                reset_result = device.ResetCounter(counter)
            else:
                reset_result = device.counter_reset(counter)

            if reset_result == 0:
                print("  ✓ Counter {} reset successful".format(counter))
            else:
                print(
                    "  ⚠️  Counter {} reset returned: {}".format(counter, reset_result)
                )

            # Read counter value
            if hasattr(device, "ReadCounter"):
                value = device.ReadCounter(counter)
            else:
                value = device.counter_read(counter)

            if value >= 0:
                print("  ✓ Counter {} value: {}".format(counter, value))
                results[counter] = True
            else:
                print("  ❌ Counter {} ERROR: Invalid value {}".format(counter, value))
                results[counter] = False

        except Exception as e:
            print("  ❌ Counter {} ERROR: {}".format(counter, e))
            results[counter] = False

    return results


def validate_dome_config(config_file):
    """Validate a dome configuration file."""
    print_section("Validating Dome Configuration")

    if not os.path.exists(config_file):
        print("❌ Configuration file not found: {}".format(config_file))
        return False

    try:
        with open(config_file, "r") as f:
            config = json.load(f)

        print("✓ Configuration file loaded successfully")

        # Check required sections
        required_sections = ["pins", "calibration", "hardware"]
        for section in required_sections:
            if section in config:
                print("✓ Section '{}' found".format(section))
            else:
                print("❌ Required section '{}' missing".format(section))
                return False

        # Check required pins
        required_pins = [
            "encoder_a",
            "encoder_b",
            "home_switch",
            "shutter_upper_limit",
            "shutter_lower_limit",
            "dome_rotate",
            "dome_direction",
            "shutter_move",
            "shutter_direction",
        ]

        pins = config.get("pins", {})
        for pin_name in required_pins:
            if pin_name in pins:
                pin_value = pins[pin_name]
                print("✓ Pin '{}': {}".format(pin_name, pin_value))

                # Validate pin ranges
                if pin_name in ["encoder_a", "encoder_b", "home_switch"]:
                    # Digital inputs (1-5)
                    if not (1 <= pin_value <= 5):
                        print(
                            "  ⚠️  Digital input pin {} out of range (1-5)".format(
                                pin_value
                            )
                        )
                elif "analog" in pin_name or "limit" in pin_name:
                    # Analog inputs (1-2)
                    if not (1 <= pin_value <= 2):
                        print(
                            "  ⚠️  Analog input channel {} out of range (1-2)".format(
                                pin_value
                            )
                        )
                else:
                    # Digital outputs (1-8)
                    if not (1 <= pin_value <= 8):
                        print(
                            "  ⚠️  Digital output pin {} out of range (1-8)".format(
                                pin_value
                            )
                        )
            else:
                print("❌ Required pin '{}' missing".format(pin_name))
                return False

        # Check for pin conflicts
        print("\nChecking for pin conflicts...")
        used_digital_inputs = []
        used_digital_outputs = []
        used_analog_inputs = []

        digital_input_pins = ["encoder_a", "encoder_b", "home_switch"]
        digital_output_pins = [
            "dome_rotate",
            "dome_direction",
            "shutter_move",
            "shutter_direction",
        ]
        analog_input_pins = ["shutter_upper_limit", "shutter_lower_limit"]

        for pin_name in digital_input_pins:
            pin_value = pins[pin_name]
            if pin_value in used_digital_inputs:
                print("❌ Digital input pin {} used multiple times".format(pin_value))
                return False
            used_digital_inputs.append(pin_value)

        for pin_name in digital_output_pins:
            pin_value = pins[pin_name]
            if pin_value in used_digital_outputs:
                print("❌ Digital output pin {} used multiple times".format(pin_value))
                return False
            used_digital_outputs.append(pin_value)

        for pin_name in analog_input_pins:
            pin_value = pins[pin_name]
            if pin_value in used_analog_inputs:
                print("❌ Analog input channel {} used multiple times".format(pin_value))
                return False
            used_analog_inputs.append(pin_value)

        print("✓ No pin conflicts detected")

        # Test the configuration with actual hardware
        print("\nTesting configuration with K8055 device...")
        mock_mode = config.get("hardware", {}).get("mock_mode", True)
        device_port = config.get("hardware", {}).get("device_port", 0)

        device = create_test_device(mock_mode=mock_mode, device_port=device_port)
        if device:
            print("✓ K8055 device created with configuration settings")
            return True
        else:
            print("❌ Failed to create K8055 device with configuration")
            return False

    except json.JSONDecodeError as e:
        print("❌ Invalid JSON in configuration file: {}".format(e))
        return False
    except Exception as e:
        print("❌ Error validating configuration: {}".format(e))
        return False


def interactive_mode():
    """Interactive pin testing mode."""
    print_header("K8055 Interactive Pin Testing Mode")

    device = create_test_device(mock_mode=True, device_port=0)
    if not device:
        print("❌ Cannot start interactive mode without K8055 device")
        return

    print("\nCommands:")
    print("  don <pin>     - Digital output pin ON (1-8)")
    print("  doff <pin>    - Digital output pin OFF (1-8)")
    print("  din <pin>     - Read digital input pin (1-5)")
    print("  ain <channel> - Read analog input channel (1-2)")
    print("  counter <ch>  - Read counter channel (1-2)")
    print("  reset <ch>    - Reset counter channel (1-2)")
    print("  test-all      - Run all pin tests")
    print("  help          - Show this help")
    print("  quit          - Exit interactive mode")

    while True:
        try:
            # Python 2/3 compatible input
            cmd = input_func("\nK8055> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if cmd == "quit" or cmd == "q":
            break
        elif cmd == "help" or cmd == "h":
            print("\nCommands available:")
            print(
                "  don <pin>, doff <pin>, din <pin>, ain <ch>, counter <ch>, reset <ch>"
            )
            print("  test-all, help, quit")
        elif cmd == "test-all":
            test_digital_outputs(device)
            test_digital_inputs(device)
            test_analog_inputs(device)
            test_counters(device)
        elif cmd.startswith("don "):
            try:
                pin = int(cmd.split()[1])
                if hasattr(device, "SetDigitalChannel"):
                    result = device.SetDigitalChannel(pin)
                else:
                    result = device.digital_on(pin)
                print(
                    "Digital pin {} ON: {}".format(
                        pin, "Success" if result == 0 else "Failed"
                    )
                )
            except (ValueError, IndexError):
                print("Usage: don <pin_number>")
        elif cmd.startswith("doff "):
            try:
                pin = int(cmd.split()[1])
                if hasattr(device, "ClearDigitalChannel"):
                    result = device.ClearDigitalChannel(pin)
                else:
                    result = device.digital_off(pin)
                print(
                    "Digital pin {} OFF: {}".format(
                        pin, "Success" if result == 0 else "Failed"
                    )
                )
            except (ValueError, IndexError):
                print("Usage: doff <pin_number>")
        elif cmd.startswith("din "):
            try:
                pin = int(cmd.split()[1])
                if hasattr(device, "ReadDigitalChannel"):
                    value = device.ReadDigitalChannel(pin)
                else:
                    value = device.digital_in(pin)
                print(
                    "Digital input pin {}: {} {}".format(
                        pin, value, "(HIGH)" if value else "(LOW)"
                    )
                )
            except (ValueError, IndexError):
                print("Usage: din <pin_number>")
        elif cmd.startswith("ain "):
            try:
                channel = int(cmd.split()[1])
                if hasattr(device, "ReadAnalogChannel"):
                    value = device.ReadAnalogChannel(channel)
                else:
                    value = device.analog_in(channel)
                print(
                    "Analog input channel {}: {} ({}%)".format(
                        channel, value, round(value / 255.0 * 100, 1)
                    )
                )
            except (ValueError, IndexError):
                print("Usage: ain <channel_number>")
        elif cmd.startswith("counter "):
            try:
                counter = int(cmd.split()[1])
                if hasattr(device, "ReadCounter"):
                    value = device.ReadCounter(counter)
                else:
                    value = device.counter_read(counter)
                print("Counter {}: {}".format(counter, value))
            except (ValueError, IndexError):
                print("Usage: counter <counter_number>")
        elif cmd.startswith("reset "):
            try:
                counter = int(cmd.split()[1])
                if hasattr(device, "ResetCounter"):
                    result = device.ResetCounter(counter)
                else:
                    result = device.counter_reset(counter)
                print(
                    "Counter {} reset: {}".format(
                        counter, "Success" if result == 0 else "Failed"
                    )
                )
            except (ValueError, IndexError):
                print("Usage: reset <counter_number>")
        elif cmd == "":
            continue
        else:
            print(
                "Unknown command: {}. Type 'help' for available commands.".format(cmd)
            )


def show_pin_help():
    """Show K8055 pin mapping and usage information."""
    print_header("K8055 Pin Mapping and Usage Guide")

    print(
        """
K8055 USB Interface Board Pin Layout:
=====================================

DIGITAL OUTPUTS (8 pins):
  Pin 1-8: Can drive relays, LEDs, etc.
  Used for: Dome rotation control, shutter control

DIGITAL INPUTS (5 pins):
  Pin 1-5: Read switches, sensors, etc.
  Used for: Home switch, encoder signals

ANALOG INPUTS (2 channels):
  Channel 1-2: Read 0-255 (0-5V analog signals)
  Used for: Shutter limit sensors

COUNTERS (2 channels):
  Counter 1-2: Count digital input transitions
  Used for: Encoder position tracking

Dome Driver Pin Assignments:
===========================

INPUTS:
  encoder_a: Digital input (1-5) - Encoder A signal
  encoder_b: Digital input (1-5) - Encoder B signal
  home_switch: Digital input (1-5) - Home position sensor
  shutter_upper_limit: Analog input (1-2) - Shutter fully open sensor
  shutter_lower_limit: Analog input (1-2) - Shutter fully closed sensor

OUTPUTS:
  dome_rotate: Digital output (1-8) - Enable dome rotation motor
  dome_direction: Digital output (1-8) - Set dome rotation direction (CW/CCW)
  shutter_move: Digital output (1-8) - Enable shutter motor
  shutter_direction: Digital output (1-8) - Set shutter direction (open/close)

Common Pin Configuration Issues:
===============================

1. Pin Conflicts: Same pin used for multiple functions
2. Invalid Pin Numbers: Outside valid ranges (1-5 for digital inputs, 1-8 for outputs)
3. Wrong Pin Types: Using digital pin for analog function or vice versa
4. Hardware Wiring: Physical connections don't match configuration

Example Valid Configuration:
===========================
{
  "pins": {
    "encoder_a": 1,           // Digital input pin 1
    "encoder_b": 2,           // Digital input pin 2
    "home_switch": 3,         // Digital input pin 3
    "shutter_upper_limit": 1, // Analog input channel 1
    "shutter_lower_limit": 2, // Analog input channel 2
    "dome_rotate": 1,         // Digital output pin 1
    "dome_direction": 2,      // Digital output pin 2
    "shutter_move": 3,        // Digital output pin 3
    "shutter_direction": 4    // Digital output pin 4
  }
}
"""
    )


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="K8055 Pin Configuration and Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python k8055_pin_tester.py --interactive
  python k8055_pin_tester.py --config examples/dome_config_production.json
  python k8055_pin_tester.py --test-all
  python k8055_pin_tester.py --help-pins
        """,
    )

    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Start interactive pin testing mode",
    )
    parser.add_argument(
        "--config", "-c", type=str, help="Validate a dome configuration file"
    )
    parser.add_argument(
        "--test-all", "-t", action="store_true", help="Run all pin tests systematically"
    )
    parser.add_argument(
        "--help-pins",
        "-p",
        action="store_true",
        help="Show K8055 pin mapping and usage guide",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Use mock mode (default: True)",
    )
    parser.add_argument(
        "--hardware",
        action="store_true",
        help="Use real hardware (CAUTION: Only with real K8055)",
    )
    parser.add_argument(
        "--port", type=int, default=0, help="K8055 device port (0-3, default: 0)"
    )

    args = parser.parse_args()

    if args.help_pins:
        show_pin_help()
        return

    if args.interactive:
        interactive_mode()
        return

    if args.config:
        if validate_dome_config(args.config):
            print("\n✅ Configuration validation passed!")
        else:
            print("\n❌ Configuration validation failed!")
            sys.exit(1)
        return

    if args.test_all:
        print_header("K8055 Comprehensive Pin Testing")

        mock_mode = not args.hardware
        device = create_test_device(mock_mode=mock_mode, device_port=args.port)

        if not device:
            print("❌ Cannot run tests without K8055 device")
            sys.exit(1)

        # Run all tests
        digital_out_results = test_digital_outputs(device)
        digital_in_results = test_digital_inputs(device)
        analog_in_results = test_analog_inputs(device)
        counter_results = test_counters(device)

        # Summary
        print_section("Test Summary")
        total_tests = 0
        passed_tests = 0

        for test_name, results in [
            ("Digital Outputs", digital_out_results),
            ("Digital Inputs", digital_in_results),
            ("Analog Inputs", analog_in_results),
            ("Counters", counter_results),
        ]:
            if isinstance(results, dict):
                test_count = len(results)
                passed_count = sum(1 for v in results.values() if v)
                total_tests += test_count
                passed_tests += passed_count
                print("{}: {}/{} passed".format(test_name, passed_count, test_count))

        print("\nOverall: {}/{} tests passed".format(passed_tests, total_tests))

        if passed_tests == total_tests:
            print("🎉 All K8055 pin tests passed!")
        else:
            print("⚠️  Some K8055 pin tests failed. Check hardware connections.")

        return

    # No arguments provided
    parser.print_help()


if __name__ == "__main__":
    main()
