#!/usr/bin/env python
"""
INDI Dome Driver - Main dome control module.

This module provides the main Dome class for controlling astronomical observatory
dome operations including rotation, home positioning, and shutter control using
the Velleman K8055 USB interface board.
"""
import sys
import time

import pyk8055_wrapper
from config import load_config


class Dome:
    def __init__(self, config_file="dome_config.json"):
        print("Creating new Dome object")
        sys.stdout.flush()

        # Load configuration - handle both file path and config dict
        if isinstance(config_file, dict):
            self.config = config_file
        else:
            self.config = load_config(config_file)

        # INPUTS
        # Encoder A input pin
        self.A = self.config["pins"]["encoder_a"]
        # Encoder B input pin
        self.B = self.config["pins"]["encoder_b"]
        # Home switch input pin
        self.HOME = self.config["pins"]["home_switch"]
        # Azimuth direction is wired into input 4
        # self.DIR_PIN = 4
        # Shutter upper limit analog channel
        self.UPPER = self.config["pins"]["shutter_upper_limit"]
        # Shutter lower limit analog channel
        self.LOWER = self.config["pins"]["shutter_lower_limit"]

        # Dome rotation On/Off Output
        self.DOME_ROTATE = self.config["pins"]["dome_rotate"]
        # Dome direction CW/CCW Output
        self.DOME_DIR = self.config["pins"]["dome_direction"]

        # Dome shutter On/Off Output
        self.SHUTTER_MOVE = self.config["pins"]["shutter_move"]
        # Dome shutter Open/Close Output
        self.SHUTTER_DIR = self.config["pins"]["shutter_direction"]

        self.CW = False
        self.CCW = True

        self.is_home = False
        self.is_turning = False
        self.dir = self.CW

        self.is_open = False
        self.is_closed = True
        self.is_opening = False
        self.is_closing = False

        # Configuration-based timing and calibration
        self.POLL = self.config["calibration"]["poll_interval"]
        self.position = 0.0
        self.HOME_POS = self.config["calibration"].get(
            "home_position", 0.0
        )  # Default to 0 if missing
        self.TICKS_TO_DEG = self.config["calibration"].get(
            "ticks_to_degrees", 1.0
        )  # Default ratio

        # Shutter timing constants
        if self.config.get("testing", {}).get("smoke_test", False):
            self.MAX_OPEN_TIME = self.config["testing"]["smoke_test_timeout"]
            print("SMOKE TEST MODE: Using short timeout of {}s"
                  .format(self.MAX_OPEN_TIME))
        else:
            self.MAX_OPEN_TIME = (
                30.0  # Maximum time to wait for shutter operation (seconds)
            )

        # Initialize hardware interface
        mock_mode = self.config["hardware"]["mock_mode"]
        device_port = self.config["hardware"]["device_port"]
        self.dome = pyk8055_wrapper.device(port=device_port, mock=mock_mode)
        print("done.")
        sys.stdout.flush()

    def cw(self, amount=0, to_home=False):
        print("Rotate CW...")
        sys.stdout.flush()
        self.set_rotation(self.CW)
        print("dir set...")
        sys.stdout.flush()
        if to_home:
            # rotate until home switch triggers
            print("rotating to home pos...")
            sys.stdout.flush()
            self.home()
        else:
            # rotate by "amount" degrees
            print("rotating by amount %d..." % (amount))
            sys.stdout.flush()
            self.rotation(amount)
        print("done.")
        sys.stdout.flush()

    def ccw(self, amount=0, to_home=False):
        self.set_rotation(self.CCW)
        if to_home:
            # rotate until home switch triggers
            self.home()
        else:
            # rotate by "amount" degrees.
            # amount == time to rotate
            self.rotation(amount)

    # Default to relay "off"
    def set_rotation(self, dir):
        self.dir = dir
        if dir == self.CCW:
            self.dome.digital_on(self.DOME_DIR)
        else:
            self.dome.digital_off(self.DOME_DIR)

    def home(self):
        print("Moving to home from position %f" % self.get_pos())
        sys.stdout.flush()
        while self.dome.digital_in(self.HOME) == 0:
            self.is_home = False
            if not self.is_turning:
                print("Starting rotation...")
                sys.stdout.flush()
                self.dome.digital_on(self.DOME_ROTATE)
                self.is_turning = True
            # TODO: add watchdog
            time.sleep(self.POLL)
            print(".")
            sys.stdout.flush()
        self.dome.digital_off(self.DOME_ROTATE)
        self.is_turning = False
        self.is_home = True
        self.set_pos(self.HOME_POS)
        print("done.")

    def rotation(self, amount=0):
        start_pos = self.get_pos()
        target_pos = start_pos + (amount * self.TICKS_TO_DEG)
        while (
            self.dome.counter_read(self.A) < target_pos
        ):  # Bug: only works for one direction
            if not self.is_turning:
                self.dome.digital_on(self.DOME_ROTATE)
                self.is_turning = True
            time.sleep(self.POLL)
        self.dome.digital_off(self.DOME_ROTATE)
        self.is_turning = False

    def get_pos(self):
        curr_ticks = self.dome.counter_read(self.A)
        self.position = curr_ticks * self.TICKS_TO_DEG
        return self.position

    # Reset the tick counters to 0 when you reach HOME
    def set_pos(self, in_pos):
        if in_pos == self.HOME_POS:
            self.counter_reset()
        self.position = in_pos

    def counter_reset(self):
        self.dome.counter_reset(self.A)
        self.dome.counter_reset(self.B)

    def counter_read(self):
        encoder_ticks = {
            "A": self.dome.counter_read(self.A),
            "B": self.dome.counter_read(self.B),
        }
        print(encoder_ticks)
        return encoder_ticks

    # Safety and status check methods
    def isHome(self):
        """Check if dome is at home position by reading home switch"""
        try:
            # Read the actual home switch state
            home_switch_active = self.dome.digital_in(self.HOME)
            if home_switch_active:
                self.is_home = True
            else:
                self.is_home = False
            return self.is_home
        except Exception as e:
            raise Exception("Hardware error reading home switch: {}".format(e))

    def isClosed(self):
        """Check if shutter is closed"""
        return self.is_closed

    def isOpen(self):
        """Check if shutter is open"""
        return self.is_open

    def setup_shutter(self):
        """Initialize shutter hardware - only works at home position"""
        if not self.isHome():
            print("ERROR: Cannot setup shutter - dome is not at home position")
            return False
        print("Setting up shutter hardware...")
        # Add any shutter initialization code here
        print("Shutter setup complete.")
        return True

    def get_shutter_limits(self):
        """
        Read shutter limit switches
        Note: These are physical switches that stop motor power, not telemetry
        They indicate if shutter is at the physical limit positions

        Returns:
            dict: Dictionary with 'upper_limit' and 'lower_limit' analog values (0-255)
        """
        upper_limit = self.dome.analog_in(self.UPPER)
        lower_limit = self.dome.analog_in(self.LOWER)
        return {"upper_limit": upper_limit, "lower_limit": lower_limit}

    def shutter_open(self):
        """
        Start opening the shutter
        Shutter will stop automatically when it hits the upper limit switch
        Software should wait MAX_OPEN_TIME then assume it's done
        """
        if not self.isHome():
            print("ERROR: Cannot operate shutter - dome is not at home position")
            return False
        if self.is_opening or self.is_closing:
            print("ERROR: Shutter operation already in progress")
            return False
        print("Sending OPEN signal to shutter...")
        self.dome.digital_on(self.SHUTTER_MOVE)
        self.dome.digital_off(self.SHUTTER_DIR)  # Direction for opening
        self.is_opening = True
        self.is_closing = False
        return True

    def shutter_close(self):
        """
        Start closing the shutter
        Shutter will stop automatically when it hits the lower limit switch
        Software should wait MAX_OPEN_TIME then assume it's done
        """
        if not self.isHome():
            print("ERROR: Cannot operate shutter - dome is not at home position")
            return False

        if self.is_opening or self.is_closing:
            print("ERROR: Shutter operation already in progress")
            return False

        print("Sending CLOSE signal to shutter...")
        self.dome.digital_on(self.SHUTTER_MOVE)
        self.dome.digital_on(self.SHUTTER_DIR)  # Direction for closing
        self.is_closing = True
        self.is_opening = False
        return True

    def rotation_stop(self):
        """
        Stop dome rotation (emergency stop)
        """
        print("Stopping dome rotation...")
        self.dome.digital_off(self.DOME_ROTATE)
        self.dome.digital_off(self.DOME_DIR)
        self.is_turning = False
        print("Dome rotation stopped.")

    def shutter_stop(self):
        """
        Stop shutter movement (emergency stop or end of timer)
        """
        print("Stopping shutter movement...")
        self.dome.digital_off(self.SHUTTER_MOVE)
        self.dome.digital_off(self.SHUTTER_DIR)
        self.is_opening = False
        self.is_closing = False
        print("Shutter movement stopped.")

    def wait_for_shutter_operation(self, operation_name):
        """
        Wait for shutter operation to complete
        Since there's no telemetry, we just wait MAX_OPEN_TIME
        """
        print("Waiting {}s for {} to complete..."
              .format(self.MAX_OPEN_TIME, operation_name))
        elapsed = 0
        while elapsed < self.MAX_OPEN_TIME:
            time.sleep(self.POLL)
            elapsed += self.POLL
            print("  {}... {:.1f}s elapsed".format(operation_name, elapsed))

        # Stop the movement signal after timeout
        self.shutter_stop()
        print(
            "{} operation completed (timed out at {}s)"
            .format(operation_name, self.MAX_OPEN_TIME)
        )

    def setOpen(self):
        """Set shutter state to open"""
        self.is_open = True
        self.is_closed = False
        print("Shutter state set to OPEN")

    def setClosed(self):
        """Set shutter state to closed"""
        self.is_closed = True
        self.is_open = False
        print("Shutter state set to CLOSED")
