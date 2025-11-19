#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
INDI Dome State Persistence Module - Python 2.7 Compatible

This module provides state persistence for the INDI K8055 dome driver.
It saves and restores all dome sensor states between script executions.

Persisted States:
- Position and encoder values
- Home switch state
- Shutter states (open/closed/opening/closing)
- Movement states (turning direction)
- Calibration parameters

Compatible with Python 2.7 - no f-strings or other Python 3 features.
"""

import json
import os
import sys
from datetime import datetime


class DomePersistence(object):
    """Handles persistence of all dome states between script executions"""

    def __init__(self, state_file=None):
        """Initialize persistence with optional custom state file path"""
        if state_file is None:
            # Use a standard location in the driver directory
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.state_file = os.path.join(script_dir, "..", "..", "dome_state.json")
        else:
            self.state_file = state_file

        # Ensure state file directory exists
        state_dir = os.path.dirname(self.state_file)
        if not os.path.exists(state_dir):
            try:
                os.makedirs(state_dir)
            except OSError:
                pass  # Directory might exist already

    def save_dome_state(self, dome, script_name=None):
        """
        Save complete dome state to persistence file

        Args:
            dome: Dome object with current state
            script_name: Name of script saving state (optional)

        Returns:
            bool: True if save successful, False otherwise
        """
        try:
            # Get encoder values safely
            try:
                encoder_values = dome.counter_read()
                encoder_a = encoder_values.get("A", 0)
                encoder_b = encoder_values.get("B", 0)
            except (AttributeError, TypeError):
                encoder_a = 0
                encoder_b = 0

            # Get connection state
            try:
                # Check if the underlying K8055 device is connected
                device_connected = getattr(dome.dome.k8055_device, "is_open", False)
            except (AttributeError, TypeError):
                device_connected = False

            # Get current position - use attribute directly to avoid encoder recalc
            try:
                # Use stored position attrib, not get_pos(); no recalcs from encoders
                current_position = getattr(dome, "position", 0.0)
            except (AttributeError, TypeError):
                # Fallback to get_pos() if position attribute doesn't exist
                try:
                    current_position = dome.get_pos()
                except (AttributeError, TypeError):
                    current_position = 0.0

            # Build complete state
            state = {
                "timestamp": datetime.now().isoformat(),
                "script": script_name or "unknown",
                # Position and movement
                "position": current_position,
                "home_position": getattr(dome, "HOME_POS", 0.0),
                "degrees_to_ticks": getattr(dome, "DEG_TO_TICKS", 1.0),
                # Encoder states
                "encoder_a": encoder_a,
                "encoder_b": encoder_b,
                # Movement states
                "is_home": getattr(dome, "is_home", False),
                "is_turning": getattr(dome, "is_turning", False),
                "direction": getattr(dome, "dir", False),  # CW=False, CCW=True
                # Shutter states
                "shutter_open": getattr(dome, "is_open", False),
                "shutter_closed": getattr(dome, "is_closed", True),
                "shutter_opening": getattr(dome, "is_opening", False),
                "shutter_closing": getattr(dome, "is_closing", False),
                # Connection state
                "device_connected": device_connected,
                # Hardware configuration
                "pins": {
                    "encoder_a": getattr(dome, "A", 1),
                    "encoder_b": getattr(dome, "B", 2),
                    "home_switch": getattr(dome, "HOME", 3),
                    "dome_rotate": getattr(dome, "DOME_ROTATE", 1),
                    "dome_direction": getattr(dome, "DOME_DIR", 2),
                    "shutter_move": getattr(dome, "SHUTTER_MOVE", 3),
                    "shutter_direction": getattr(dome, "SHUTTER_DIR", 4),
                },
                # Timing configuration
                "poll_interval": getattr(dome, "POLL", 0.1),
                "max_open_time": getattr(dome, "MAX_OPEN_TIME", 30.0),
            }

            # Write state to file
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)

            print(
                "Dome state saved: position="
                "{:.2f}deg, home={}, turning={}, connected={}".format(
                    current_position,
                    state["is_home"],
                    state["is_turning"],
                    state["device_connected"],
                )
            )
            return True

        except Exception as e:
            print("Error saving dome state: {}".format(e))
            return False

    def load_dome_state(self):
        """
        Load dome state from persistence file

        Returns:
            dict: State dictionary or None if no state/error
        """
        try:
            if not os.path.exists(self.state_file):
                return None

            with open(self.state_file, "r") as f:
                state = json.load(f)

            print(
                "Dome state loaded from {}: position={:.2f}deg, saved by {}".format(
                    state.get("timestamp", "unknown"),
                    state.get("position", 0.0),
                    state.get("script", "unknown"),
                )
            )
            return state

        except Exception as e:
            print("Error loading dome state: {}".format(e))
            return None

    def restore_dome_state(self, dome, state=None):
        """
        Restore dome object state from persistence data

        Args:
            dome: Dome object to restore state to
            state: State dict (optional, will load if None)

        Returns:
            bool: True if restore successful, False otherwise
        """
        try:
            if state is None:
                state = self.load_dome_state()

            if state is None:
                print("No state to restore")
                return False

            # Restore position and calibration
            dome.position = state.get("position", 0.0)
            dome.HOME_POS = state.get("home_position", 0.0)
            dome.DEG_TO_TICKS = state.get("degrees_to_ticks", 1.0)

            # Restore movement states
            dome.is_home = state.get("is_home", False)
            dome.is_turning = state.get("is_turning", False)
            dome.dir = state.get("direction", False)

            # Restore shutter states
            dome.is_open = state.get("shutter_open", False)
            dome.is_closed = state.get("shutter_closed", True)
            dome.is_opening = state.get("shutter_opening", False)
            dome.is_closing = state.get("shutter_closing", False)

            # Restore connection state to underlying device
            device_connected = state.get("device_connected", False)
            try:
                if hasattr(dome, "dome") and hasattr(dome.dome, "k8055_device"):
                    dome.dome.k8055_device.is_open = device_connected
            except (AttributeError, TypeError):
                # If can't set connection state, just continue
                pass

            # Restore timing
            dome.POLL = state.get("poll_interval", 0.1)
            dome.MAX_OPEN_TIME = state.get("max_open_time", 30.0)

            print(
                "Dome state restored: position="
                "{:.2f}deg, home={}, turning={}, connected={}".format(
                    dome.position, dome.is_home, dome.is_turning, device_connected
                )
            )
            return True

        except Exception as e:
            print("Error restoring dome state: {}".format(e))
            return False

    def get_state_summary(self):
        """Get a summary of the current persisted state"""
        state = self.load_dome_state()
        if state is None:
            return "No persisted state available"

        summary = []
        summary.append("=== DOME STATE SUMMARY ===")
        summary.append("Saved: {}".format(state.get("timestamp", "unknown")))
        summary.append("Script: {}".format(state.get("script", "unknown")))
        summary.append("Position: {:.2f}deg".format(state.get("position", 0.0)))
        summary.append("Home: {}".format(state.get("is_home", False)))
        summary.append("Turning: {}".format(state.get("is_turning", False)))
        summary.append("Shutter Open: {}".format(state.get("shutter_open", False)))
        summary.append("Encoder A: {} ticks".format(state.get("encoder_a", 0)))
        summary.append("Encoder B: {} ticks".format(state.get("encoder_b", 0)))

        return "\n".join(summary)

    def clear_state(self):
        """Clear the persisted state file"""
        try:
            if os.path.exists(self.state_file):
                os.remove(self.state_file)
                print("Dome state cleared")
                return True
        except Exception as e:
            print("Error clearing state: {}".format(e))
        return False


def create_persistent_dome(config_file="dome_config.json", state_file=None):
    """
    Create a dome object with automatic state restoration

    Args:
        config_file: Dome configuration file or dict
        state_file: Optional custom state file path

    Returns:
        tuple: (dome_object, persistence_object)
    """
    try:
        # Import dome module
        from dome import Dome

        # Create persistence handler
        persistence = DomePersistence(state_file)

        # Create dome object
        dome = Dome(config_file)

        # Try to restore previous state
        if persistence.restore_dome_state(dome):
            print("Dome created with restored state")
        else:
            print("Dome created with fresh state")

        return dome, persistence

    except ImportError as e:
        print("Error importing dome module: {}".format(e))
        return None, None


# Convenience functions for easy script integration
def save_state(dome, script_name=None, state_file=None):
    """Convenience function to save dome state"""
    persistence = DomePersistence(state_file)
    return persistence.save_dome_state(dome, script_name)


def load_state(state_file=None):
    """Convenience function to load dome state"""
    persistence = DomePersistence(state_file)
    return persistence.load_dome_state()


def restore_state(dome, state_file=None):
    """Convenience function to restore dome state"""
    persistence = DomePersistence(state_file)
    return persistence.restore_dome_state(dome)


def show_state(state_file=None):
    """Convenience function to show state summary"""
    persistence = DomePersistence(state_file)
    print(persistence.get_state_summary())


def clear_state(state_file=None):
    """Convenience function to clear state"""
    persistence = DomePersistence(state_file)
    return persistence.clear_state()


# Example usage when run as script
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--show":
            show_state()
        elif sys.argv[1] == "--clear":
            clear_state()
        elif sys.argv[1] == "--test":
            # Test persistence functionality
            print("Testing dome persistence...")
            dome, persistence = create_persistent_dome(
                {
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
                        "degrees_to_ticks": 1.0,
                        "poll_interval": 0.1,
                    },
                    "hardware": {"mock_mode": True, "device_port": 0},
                    "testing": {"smoke_test": True, "smoke_test_timeout": 3.0},
                }
            )

            if dome and persistence:
                # Simulate some changes
                dome.position += 15.0
                dome.is_turning = True
                persistence.save_dome_state(dome, "test")
                print(persistence.get_state_summary())
        else:
            print("Usage: python persistence.py [--show|--clear|--test]")
    else:
        print("INDI Dome Persistence Module")
        print("Usage: python persistence.py [--show|--clear|--test]")
