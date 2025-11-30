#!/usr/bin/env python
"""
Configuration loader for INDI Dome Driver.

This module handles loading configuration from external files.
Users should create a 'dome_config.json' file with their specific settings.
"""

import json
import os

# Default configuration values
DEFAULT_CONFIG = {
    # Hardware pin assignments
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
    # Dome-specific calibration values
    "calibration": {
        "home_position": 0,  # Default to 0, user must calibrate
        "degrees_to_ticks": 1.0,  # Default ratio, user must calibrate
        "poll_interval": 0.5,  # Polling interval in seconds
    },
    # Hardware settings
    "hardware": {
        "mock_mode": False,  # Production default - real hardware
        "device_port": 0,  # K8055 device port
    },
    # Testing settings
    "testing": {
        "smoke_test": False,  # Use shorter timeouts for testing
        "smoke_test_timeout": 3.0,  # Short timeout for smoke tests
    },
    # Safety timeout settings
    "safety": {
        "emergency_stop_timeout": 2.0,  # Max time for emergency stop
        "operation_timeout": 60.0,  # Max time for normal operations
        "max_rotation_time": 120.0,  # Max time for full rotation
        "max_shutter_time": 30.0,  # Max time for shutter operation
    },
}


def load_config(config_file="dome_config.json"):
    """
    Load configuration from JSON file, falling back to defaults.

    Args:
        config_file (str): Path to configuration file

    Returns:
        dict: Configuration dictionary
    """
    config = DEFAULT_CONFIG.copy()

    # Check for test mode environment variable
    test_mode = os.environ.get("DOME_TEST_MODE", "").lower()
    is_smoke_mode = test_mode == "smoke"

    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                user_config = json.load(f)
                # Deep merge user config with defaults
                for section, values in user_config.items():
                    if section in config and isinstance(config[section], dict):
                        config[section].update(values)
                    else:
                        config[section] = values
            print("Loaded configuration from {}".format(config_file))
        except (IOError, json.JSONDecodeError) as e:
            print("Warning: Could not load {}: {}".format(config_file, e))
            print("Using default configuration values")
    else:
        print("Configuration file {} not found, using defaults".format(config_file))
        print("Create a dome_config.json file to customize settings")

    # Apply smoke mode adjustments if enabled
    if is_smoke_mode:
        config["testing"]["smoke_test"] = True
        config["hardware"]["mock_mode"] = True
        # Shorter safety timeouts for smoke mode
        config["safety"]["emergency_stop_timeout"] = 1.0
        config["safety"]["operation_timeout"] = 5.0
        config["safety"]["max_rotation_time"] = 10.0
        config["safety"]["max_shutter_time"] = 5.0

    return config


def create_sample_config(filename="dome_config.json.example"):
    """
    Create a sample configuration file for users to customize.

    Args:
        filename (str): Name of the sample config file to create
    """
    sample_config = {
        "_comment": (
            "INDI Dome Driver Configuration - " "Copy to dome_config.json and customize"
        ),
        "pins": {
            "_comment": "Pin assignments for K8055 interface board",
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
            "_comment": "Dome-specific calibration values - MUST be set for your dome",
            "home_position": 225,
            "degrees_to_ticks": 1.146,
            "poll_interval": 0.5,
        },
        "hardware": {
            "_comment": "Hardware interface settings",
            "mock_mode": False,
            "device_port": 0,
        },
        "testing": {
            "_comment": "Testing configuration",
            "smoke_test": True,
            "smoke_test_timeout": 3.0,
        },
    }

    with open(filename, "w") as f:
        json.dump(sample_config, f, indent=4)

    print("Created sample configuration file: {}".format(filename))
    print("Copy this to dome_config.json and customize for your dome")


if __name__ == "__main__":
    # When run directly, create a sample config file
    create_sample_config()
