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
    def degrees(self, tics):
        """
        Convert encoder tics to degrees, direction-aware.
        Uses current dome direction (self.dir).
        """
        if self.dir == self.CW:
            deg = float(tics) * self.degrees_per_tic_cw
        else:
            deg = float(-tics) * self.degrees_per_tic_ccw
        return deg

    def tics(self, degrees):
        """
        Convert degrees to encoder tics, direction-aware.
        Returns (int, decimal) tuple.
        """
        if self.dir == self.CW:
            tics_float = float(degrees) / self.degrees_per_tic_cw
        else:
            tics_float = float(degrees) / self.degrees_per_tic_ccw
        tics_int = int(tics_float)
        tics_dec = round(tics_float - tics_int, 2)
        return (tics_int, tics_dec)

    def current_position(self):
        """
        Calculate current position based on
        last known position, encoder ticks, and direction.
        Does not reset encoder or update persistent state.
        """
        encoder_ticks, _ = self.counter_read()
        pos = (self.position + self.degrees(encoder_ticks)) % 360.0
        # If home is sensed, set position to HOME_POS
        # (for safety, but do not reset encoder)
        if self.isHome():
            pos = self.HOME_POS
        return pos

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
        # Note: No shutter telemetry - uses fixed timing with auto limit switch cutoff
        # Removed erroneous shutter_upper_limit and shutter_lower_limit references

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

        # Gray Code encoder state tracking for direction detection
        self.encoder_state_history = []  # Track recent encoder states
        self.last_encoder_state = None
        self.encoder_direction = None  # CW or CCW based on Gray Code transitions
        self.encoder_errors = 0  # Count missed or invalid transitions
        self.encoder_speed = 0.0  # Calculated rotation speed (degrees/second)
        self.last_encoder_time = time.time()

        # Home switch polling optimization
        self.home_switch_history = []  # Track recent home switch readings
        self.home_signal_duration = 0.0  # Duration of current home signal (seconds)
        self.home_poll_fast = 0.05  # Fast polling rate during homing (50ms)
        self.home_poll_normal = None  # Will be set to self.POLL
        self.home_switch_debounce = 0.1  # Minimum signal duration for valid detection
        self.max_rotation_speed = 0.0  # Maximum observed rotation speed (deg/s)

        # Configuration-based timing and calibration
        self.POLL = self.config["calibration"]["poll_interval"]

        # Home switch polling optimization configuration
        self.home_poll_fast = self.config["calibration"].get("home_poll_fast", 0.05)
        self.home_switch_debounce = self.config["calibration"].get(
            "home_switch_debounce", 0.1
        )

        # Encoder calibration configuration
        self.encoder_error_threshold = self.config["calibration"].get(
            "encoder_error_threshold", 50
        )
        self.encoder_calibration_timeout = self.config["calibration"].get(
            "encoder_calibration_timeout", 180.0
        )

        self.position = 0.0
        self.HOME_POS = self.config["calibration"].get(
            "home_position", 0.0
        )  # Default to 0 if missing
        # Direction-aware encoder calibration
        self.encoder_tics_per_dome_revolution = self.config["calibration"].get(
            "encoder_tics_per_dome_revolution", [360, 360]
        )
        self.degrees_per_tic_cw = 360.0 / float(
            self.encoder_tics_per_dome_revolution[self.CW]
        )
        self.degrees_per_tic_ccw = 360.0 / float(
            self.encoder_tics_per_dome_revolution[self.CCW]
        )

        # Shutter timing constants
        if self.config.get("testing", {}).get("smoke_test", False):
            self.MAX_OPEN_TIME = self.config["testing"]["smoke_test_timeout"]
            print(
                "SMOKE TEST MODE: Using short timeout of {}s".format(self.MAX_OPEN_TIME)
            )
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

    def direction_str(self):
        """
        Get string representation of current rotation direction
        """
        return "CW" if self.dir == self.CW else "CCW"

    def cw(self):
        """
        Rotate clockwise using non-blocking control with proper relay sequencing
        """
        return self._rotate_direction(self.CW)

    def ccw(self):
        """
        Rotate counter-clockwise using non-blocking control with proper relay sequencing
        """
        return self._rotate_direction(self.CCW)

    def _rotate_direction(self, direction_value):
        """
        Internal method to handle rot in either direction (eliminates code dupe)
        """
        # Set direction first (with proper timing)
        self._set_rotation(direction_value)

        print("Rotate {}...".format(self.direction_str()))
        sys.stdout.flush()

        # Start rotation (go until aborted)
        result = self._rotation_start()
        return result

    # Default to relay "off"
    def _set_rotation(self, dir):
        """
        Set rotation direction relay with proper timing
        This method implements safe relay sequencing
        """
        self.dir = dir
        # First, ensure motor is stopped
        if self.is_turning:
            print("Warning: Setting direction while motor running - stopping first")
            self.rotation_stop()
            time.sleep(0.1)  # Brief pause for motor to stop

        # Set direction relay with proper state
        if dir == self.CCW:
            self.dome.digital_on(self.DOME_DIR)
        else:
            self.dome.digital_off(self.DOME_DIR)

        # Allow relay settling time (20ms minimum for safety)
        time.sleep(0.02)

        # Verify direction if telemetry available (DI4 connected to DO2)
        # Note: This will be implemented when direction telemetry is added

    def _rotation_start(self):
        """
        Start dome rotation in the previously set direction
        Non-blocking operation - returns immediately after starting motor
        """
        if self.is_turning:
            print("Warning: Rotation already in progress")
            return False

        print("Starting rotation in direction: {}".format(self.direction_str()))

        # Enable motor (direction should already be set via set_rotation)
        self.dome.digital_on(self.DOME_ROTATE)
        self.is_turning = True
        return True

    def rotation_stop(self):
        """
        Stop dome rotation immediately
        Non-blocking operation - disables motor and clears state
        """
        print("Stopping dome rotation...")

        # Disable motor immediately
        self.dome.digital_off(self.DOME_ROTATE)

        # Brief settling delay
        time.sleep(0.01)

        # Clear direction relay for safety
        self.dome.digital_off(self.DOME_DIR)

        # Update state
        self.update_pos()
        self.is_turning = False
        print("Dome rotation stopped.")
        return True

    def home(self):
        """
        Move dome to home position
        """
        return self.rotation(home=True)

    def _set_optimal_goto_direction(self, current_pos, target_pos):
        """
        Select optimal direction for fastest path to target position
        """
        # Calculate angular distances for both directions
        cw_distance = (target_pos - current_pos) % 360
        ccw_distance = (current_pos - target_pos) % 360

        # Choose shortest path
        if cw_distance <= ccw_distance:
            self._set_rotation(self.CW)
            distance = cw_distance
        else:
            self._set_rotation(self.CCW)
            distance = ccw_distance

        print(
            "Optimal path: {} degrees {} to target".format(
                distance, self.direction_str()
            )
        )
        return distance

    def rotation(self, azimuth=0, home=False):
        """
        Rotate dome to specified azimuth using non-blocking control

        Args:
            azimuth: Target azimuth in degrees
        """
        start_pos = self.get_pos()
        if home:
            azimuth = self.HOME_POS
            self.homes_reset()

        if azimuth == start_pos:
            print("Dome already at requested azimuth: {:.1f}".format(azimuth))
            return True

        # Set direction based on amount sign and current direction preference
        distance = self._set_optimal_goto_direction(start_pos, azimuth)

        print(
            "Rotating {} degrees from {:.1f} to {:.1f}".format(
                distance, start_pos, azimuth
            )
        )

        # Ensure we're not already moving
        if self.is_turning:
            print("Stopping current rotation before new movement...")
            self.rotation_stop()
            time.sleep(0.1)

        # Start rotation
        if not self._rotation_start():
            print("ERROR: Could not start rotation")
            return False

        if home:
            print("Homing to position {:.1f}...".format(azimuth))
            sys.stdout.flush()
            while True:
                if self.isHome():
                    print("Home switch activated.")
                    # Reset encoder when crossing home position
                    self.set_pos(self.HOME_POS)
                    break
                time.sleep(self.POLL)
        else:
            print("Rotating to azimuth {:.1f}...".format(azimuth))
            sys.stdout.flush()
            encoder_ticks = 0
            target_ticks_tuple = self.tics(distance)
            target_ticks = target_ticks_tuple[0]
            while encoder_ticks < target_ticks:
                encoder_ticks_tuple = self.counter_read()
                encoder_ticks = encoder_ticks_tuple[0]
                # TODO: Add timeout watchdog
                time.sleep(self.POLL)

        # Stop rotation when target reached
        self.rotation_stop()

        final_pos = self.get_pos()
        print("Rotation completed. Final position: {:.1f}".format(final_pos))
        return True

    def get_pos(self):
        return self.position

    def update_pos(self):
        # Called when dome stops moving: update position and reset encoder
        encoder_ticks, _ = self.counter_read()
        delta_angle = self.degrees(encoder_ticks) % 360.0
        if self.dir == self.CW:
            new_pos = (self.get_pos() + delta_angle) % 360.0
        else:
            new_pos = (self.get_pos() - delta_angle) % 360.0
        # If home is sensed, set position to HOME_POS
        if self.isHome():
            new_pos = self.HOME_POS
        self.set_pos(new_pos, reset_encoder=True)

    # Reset the tick counters to 0 when you reach target position
    def set_pos(self, in_pos, reset_encoder=False):
        encoder_ticks, _ = self.counter_read()
        print(
            "[DEBUG] Before reset: Encoder ticks: {}, Updated position: {:.1f}".format(
                encoder_ticks, in_pos
            )
        )
        # Only reset encoder when explicitly requested (e.g., at home position)
        if reset_encoder:
            self.encoder_reset()
            encoder_ticks_after, _ = self.counter_read()
            print("[DEBUG] After reset: Encoder ticks: {}".format(encoder_ticks_after))
        self.position = in_pos

    def encoder_reset(self):
        print("[DEBUG] Resetting encoder (counter 1) to zero...")
        self.dome.counter_reset(1)

    def homes_reset(self):
        self.dome.counter_reset(2)

        # Also reset Gray Code encoder tracking
        self.encoder_state_history = []
        self.last_encoder_state = None
        self.encoder_direction = None
        self.encoder_errors = 0
        self.encoder_speed = 0.0
        self.last_encoder_time = time.time()
        print("Encoder counters and Gray Code tracking reset")

    def counter_read(self):
        encoder_ticks = self.dome.counter_read(1)
        home_count = self.dome.counter_read(2)
        # print(encoder_ticks, home_count)
        return encoder_ticks, home_count

    # # 2-Bit Gray Code Encoder Implementation
    # def read_encoder_state(self):
    #     """
    #     Read both encoder channels simultaneously using ReadAllDigital
    #     Returns a 2-bit Gray Code state (0-3)
    #     """
    #     try:
    #         # Read all digital inputs as bitmask via the wrapper interface
    #         digital_state = self.dome.read_all_digital()

    #         # Extract encoder A and B bits from the bitmask
    #         # encoder_a is pin 1 (bit 0), encoder_b is pin 5 (bit 4)
    #         encoder_a = (digital_state >> (self.A - 1)) & 1
    #         encoder_b = (digital_state >> (self.B - 1)) & 1

    #         # Combine into 2-bit Gray Code state (B is MSB, A is LSB)
    #         gray_code_state = (encoder_b << 1) | encoder_a

    #         return gray_code_state

    #     except Exception as e:
    #         print("ERROR: Failed to read encoder state: {}".format(e))
    #         return None

    # def detect_encoder_direction(self, current_state):
    #     """
    #     Detect rotation direction from Gray Code state transitions

    #     Gray Code sequence for CW rotation:  00 -> 01 -> 11 -> 10 -> 00
    #     Gray Code sequence for CCW rotation: 00 -> 10 -> 11 -> 01 -> 00

    #     Args:
    #         current_state: Current 2-bit Gray Code state (0-3)

    #     Returns:
    #         'CW', 'CCW', or None if no valid transition detected
    #     """
    #     if self.last_encoder_state is None:
    #         self.last_encoder_state = current_state
    #         return "Initializing"

    #     if current_state == self.last_encoder_state:
    #         return self.direction_str()  # No change

    #     # Define valid state transitions for each direction
    #     cw_transitions = {
    #         0: 1,  # 00 -> 01
    #         1: 3,  # 01 -> 11
    #         3: 2,  # 11 -> 10
    #         2: 0,  # 10 -> 00
    #     }

    #     ccw_transitions = {
    #         0: 2,  # 00 -> 10
    #         2: 3,  # 10 -> 11
    #         3: 1,  # 11 -> 01
    #         1: 0,  # 01 -> 00
    #     }

    #     # Check for valid CW transition
    #     if (
    #         self.last_encoder_state in cw_transitions
    #         and cw_transitions[self.last_encoder_state] == current_state
    #     ):
    #         direction = "CW"
    #     # Check for valid CCW transition
    #     elif (
    #         self.last_encoder_state in ccw_transitions
    #         and ccw_transitions[self.last_encoder_state] == current_state
    #     ):
    #         direction = "CCW"
    #     else:
    #         # Invalid transition - possible encoder error or missed step
    #         self.encoder_errors += 1
    #         print(
    #             "WARNING: Invalid encoder transition: {} -> {}".format(
    #                 self.last_encoder_state, current_state
    #             )
    #         )
    #         direction = None

    #     self.last_encoder_state = current_state
    #     return direction

    # Safety and status check methods
    def isHome(self):
        """Check if dome is at home position by reading home switch"""
        try:
            # Read the actual home switch state
            self.is_home = self.dome.digital_in(self.HOME)
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

    # Note: get_shutter_limits() method removed - no shutter telemetry in this design
    # Shutter uses fixed timing with automatic limit switch cutoff (hw stops motor)

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
        self.dome.digital_off(self.SHUTTER_DIR)  # Direction for opening
        self.dome.digital_on(self.SHUTTER_MOVE)
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
        self.dome.digital_on(self.SHUTTER_DIR)  # Direction for closing
        self.dome.digital_on(self.SHUTTER_MOVE)
        self.is_closing = True
        self.is_opening = False
        return True

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
        print(
            "Waiting {}s for {} to complete...".format(
                self.MAX_OPEN_TIME, operation_name
            )
        )
        elapsed = 0
        while elapsed < self.MAX_OPEN_TIME:
            time.sleep(self.POLL)
            elapsed += self.POLL
            print("  {}... {:.1f}s elapsed".format(operation_name, elapsed))

        # Stop the movement signal after timeout
        self.shutter_stop()
        print(
            "{} operation completed (timed out at {}s)".format(
                operation_name, self.MAX_OPEN_TIME
            )
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
