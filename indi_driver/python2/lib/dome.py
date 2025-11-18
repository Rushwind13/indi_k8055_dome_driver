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
        self.TICKS_TO_DEG = self.config["calibration"].get(
            "ticks_to_degrees", 1.0
        )  # Default ratio

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

    def cw(self, amount=0, to_home=False):
        """
        Rotate clockwise using non-blocking control with proper relay sequencing
        """
        return self._rotate_direction("CW", self.CW, amount, to_home)

    def ccw(self, amount=0, to_home=False):
        """
        Rotate counter-clockwise using non-blocking control with proper relay sequencing
        """
        return self._rotate_direction("CCW", self.CCW, amount, to_home)

    def _rotate_direction(self, direction_name, direction_value, amount, to_home):
        """
        Internal method to handle rot in either direction (eliminates code dupe)
        """
        print("Rotate {}...".format(direction_name))
        sys.stdout.flush()

        # Set direction first (with proper timing)
        self.set_rotation(direction_value)
        print("dir set...")
        sys.stdout.flush()

        if to_home:
            # rotate until home switch triggers
            print("rotating to home pos...")
            sys.stdout.flush()
            return self.home()
        else:
            # rotate by "amount" degrees
            print("rotating by amount {}...".format(amount))
            sys.stdout.flush()
            result = self.rotation(amount)
            print("done.")
            sys.stdout.flush()
            return result

    # Default to relay "off"
    def set_rotation(self, dir):
        """
        Set rotation direction relay with proper timing
        This method implements safe relay sequencing
        """
        self.dir = dir
        # First, ensure motor is stopped
        if self.is_turning:
            print("Warning: Setting direction while motor running - stopping first")
            self.stop_rotation()
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

    def start_rotation(self):
        """
        Start dome rotation in the previously set direction
        Non-blocking operation - returns immediately after starting motor
        """
        if self.is_turning:
            print("Warning: Rotation already in progress")
            return False

        print(
            "Starting rotation in direction: {}".format(
                "CCW" if self.dir == self.CCW else "CW"
            )
        )

        # Enable motor (direction should already be set via set_rotation)
        self.dome.digital_on(self.DOME_ROTATE)
        self.is_turning = True
        return True

    def stop_rotation(self):
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
        self.is_turning = False
        print("Dome rotation stopped.")
        return True

    def home(self):
        """
        Move dome to home position with intelligent direction selection
        Automatically chooses the shortest path to home position
        """
        current_pos = self.get_pos()
        print("Moving to home from position {}".format(current_pos))
        sys.stdout.flush()

        # Ensure we're not already moving
        if self.is_turning:
            print("Stopping current rotation before homing...")
            self.stop_rotation()
            time.sleep(0.1)

        # Intelligent direction selection for shortest path to home
        direction = self._select_optimal_home_direction(current_pos)
        self.set_rotation(direction)

        # Start rotation towards home
        if not self.start_rotation():
            print("ERROR: Could not start rotation for homing")
            return False

        return self._execute_homing_sequence()

    def _select_optimal_home_direction(self, current_pos):
        """
        Select optimal direction for fastest path to home position
        """
        home_pos = self.HOME_POS

        # Calculate angular distances for both directions
        cw_distance = (home_pos - current_pos) % 360
        ccw_distance = (current_pos - home_pos) % 360

        # Choose shortest path
        if cw_distance <= ccw_distance:
            direction = self.CW
            direction_str = "CW"
            distance = cw_distance
        else:
            direction = self.CCW
            direction_str = "CCW"
            distance = ccw_distance

        print("Optimal path: {} degrees {} to home".format(distance, direction_str))
        return direction

    def _execute_homing_sequence(self):
        """
        Execute the homing sequence with enhanced polling and validation
        """
        # Initialize encoder tracking for homing
        self.encoder_direction = None
        self.encoder_errors = 0
        direction_validated = False
        expected_direction = "CW" if self.dir == self.CW else "CCW"

        # Set fast polling mode for homing optimization
        original_poll_rate = self.POLL
        self.POLL = self.home_poll_fast
        self.home_poll_normal = (
            original_poll_rate
            if self.home_poll_normal is None
            else self.home_poll_normal
        )

        # Initialize home switch signal tracking
        home_search_start = time.time()
        last_debug_time = time.time()
        debug_interval = 2.0  # Print debug info every 2 seconds

        try:
            # Poll until home switch triggers with enhanced detection
            while not self.is_home_with_validation():
                self.is_home = False

                # Update encoder tracking during homing
                if self.update_encoder_tracking():
                    if not direction_validated and self.encoder_direction is not None:
                        if self.encoder_direction == expected_direction:
                            print(
                                "OK: Home rotation direction validated: {}".format(
                                    self.encoder_direction
                                )
                            )
                            direction_validated = True
                        else:
                            print(
                                "WARNING: Home direction mismatch: "
                                "Expected {}, Encoder {}".format(
                                    expected_direction, self.encoder_direction
                                )
                            )

                # Check for timeout with enhanced error reporting
                elapsed = time.time() - home_search_start
                if elapsed > self.MOVE_TIMEOUT:
                    raise Exception(
                        "Timed out waiting for home switch after %.1f seconds" % elapsed
                    )

                # Enhanced debug output with timing and speed information
                if time.time() - last_debug_time >= debug_interval:
                    home_state = self.dome.digital_in(self.HOME)
                    encoder_state = self.read_encoder_state()
                    print(
                        "Homing: elapsed=%.1fs, home_pin=%d, "
                        "encoder=%s, direction=%s, speed=%.2f deg/s"
                        % (
                            elapsed,
                            home_state,
                            encoder_state,
                            self.encoder_direction or "unknown",
                            self.encoder_speed,
                        )
                    )
                    last_debug_time = time.time()

                time.sleep(self.POLL)
                print(".")
                sys.stdout.flush()
        finally:
            # Always restore normal polling rate
            self.POLL = self.home_poll_normal

        # Stop rotation when home found
        self.stop_rotation()
        self.is_home = True
        self.set_pos(self.HOME_POS)
        print("done.")
        return True

    def rotation(self, amount=0):
        """
        Rotate dome by specified amount using non-blocking control
        Fixed: Now supports bidirectional rotation (CW and CCW)

        Args:
            amount: Degrees to rotate (positive=CW, negative=CCW)
        """
        start_pos = self.get_pos()

        # Determine direction based on amount sign
        if amount == 0:
            print("No rotation requested (amount=0)")
            return True

        # Set direction based on amount sign and current direction preference
        if amount > 0:
            # Positive amount: rotate in current direction
            target_pos = start_pos + (amount * self.TICKS_TO_DEG)
            direction_forward = True
        else:
            # Negative amount: rotate in opposite direction
            target_pos = start_pos + (amount * self.TICKS_TO_DEG)  # amount is negative
            direction_forward = False

        print(
            "Rotating {} degrees from {:.1f} to {:.1f}".format(
                amount, start_pos, target_pos
            )
        )

        # Ensure we're not already moving
        if self.is_turning:
            print("Stopping current rotation before new movement...")
            self.stop_rotation()
            time.sleep(0.1)

        # Start rotation
        if not self.start_rotation():
            print("ERROR: Could not start rotation")
            return False

        # Initialize encoder tracking for this movement
        self.encoder_direction = None
        self.encoder_errors = 0
        expected_direction = "CW" if direction_forward else "CCW"
        direction_validated = False

        # Monitor position until target reached
        # Enhanced: Now includes 2-bit Gray Code encoder tracking
        while True:
            current_pos = self.get_pos()

            # Update encoder tracking and validate direction
            if self.update_encoder_tracking():
                if not direction_validated and self.encoder_direction is not None:
                    # Validate direction on first encoder movement
                    if self.encoder_direction == expected_direction:
                        print(
                            "OK: Encoder direction validated: {}".format(
                                self.encoder_direction
                            )
                        )
                        direction_validated = True
                    else:
                        print(
                            "WARNING: Direction mismatch: "
                            "Expected {}, Encoder {}".format(
                                expected_direction, self.encoder_direction
                            )
                        )

            # Check if we've reached the target (with small tolerance)
            position_error = abs(current_pos - target_pos)
            if position_error < (0.5 * self.TICKS_TO_DEG):  # Within 0.5 degrees
                print(
                    "Target position reached: {:.1f} (error: {:.2f} deg)".format(
                        current_pos, position_error / self.TICKS_TO_DEG
                    )
                )
                break

            # Safety check: detect if we've overshot significantly
            if direction_forward and (current_pos > target_pos + 2 * self.TICKS_TO_DEG):
                print("WARNING: Overshot target in forward direction")
                break
            elif not direction_forward and (
                current_pos < target_pos - 2 * self.TICKS_TO_DEG
            ):
                print("WARNING: Overshot target in reverse direction")
                break

            # TODO: Add timeout watchdog
            time.sleep(self.POLL)

        # Stop rotation when target reached
        self.stop_rotation()

        final_pos = self.get_pos()
        print("Rotation completed. Final position: {:.1f}".format(final_pos))
        return True

    def get_pos(self):
        curr_ticks = self.dome.counter_read(self.A)
        self.position = curr_ticks  # * self.TICKS_TO_DEG
        return self.position

    # Reset the tick counters to 0 when you reach HOME
    def set_pos(self, in_pos):
        if in_pos == self.HOME_POS:
            self.counter_reset()
        self.position = in_pos

    def counter_reset(self):
        self.dome.counter_reset(self.A)
        self.dome.counter_reset(self.B)

        # Also reset Gray Code encoder tracking
        self.encoder_state_history = []
        self.last_encoder_state = None
        self.encoder_direction = None
        self.encoder_errors = 0
        self.encoder_speed = 0.0
        self.last_encoder_time = time.time()
        print("Encoder counters and Gray Code tracking reset")

    def counter_read(self):
        encoder_ticks = {
            "A": self.dome.counter_read(self.A),
            "B": self.dome.counter_read(self.B),
        }
        print(encoder_ticks)
        return encoder_ticks

    # 2-Bit Gray Code Encoder Implementation
    def read_encoder_state(self):
        """
        Read both encoder channels simultaneously using ReadAllDigital
        Returns a 2-bit Gray Code state (0-3)
        """
        try:
            # Read all digital inputs as bitmask via the wrapper interface
            digital_state = self.dome.read_all_digital()

            # Extract encoder A and B bits from the bitmask
            # encoder_a is pin 1 (bit 0), encoder_b is pin 5 (bit 4)
            encoder_a = (digital_state >> (self.A - 1)) & 1
            encoder_b = (digital_state >> (self.B - 1)) & 1

            # Combine into 2-bit Gray Code state (B is MSB, A is LSB)
            gray_code_state = (encoder_b << 1) | encoder_a

            return gray_code_state

        except Exception as e:
            print("ERROR: Failed to read encoder state: {}".format(e))
            self.encoder_errors += 1
            return None

    def detect_encoder_direction(self, current_state):
        """
        Detect rotation direction from Gray Code state transitions

        Gray Code sequence for CW rotation:  00 -> 01 -> 11 -> 10 -> 00
        Gray Code sequence for CCW rotation: 00 -> 10 -> 11 -> 01 -> 00

        Args:
            current_state: Current 2-bit Gray Code state (0-3)

        Returns:
            'CW', 'CCW', or None if no valid transition detected
        """
        if self.last_encoder_state is None:
            self.last_encoder_state = current_state
            return "Initializing"

        if current_state == self.last_encoder_state:
            return "No change"  # No change

        # Define valid state transitions for each direction
        cw_transitions = {
            0: 1,  # 00 -> 01
            1: 3,  # 01 -> 11
            3: 2,  # 11 -> 10
            2: 0,  # 10 -> 00
        }

        ccw_transitions = {
            0: 2,  # 00 -> 10
            2: 3,  # 10 -> 11
            3: 1,  # 11 -> 01
            1: 0,  # 01 -> 00
        }

        # Check for valid CW transition
        if (
            self.last_encoder_state in cw_transitions
            and cw_transitions[self.last_encoder_state] == current_state
        ):
            direction = "CW"
        # Check for valid CCW transition
        elif (
            self.last_encoder_state in ccw_transitions
            and ccw_transitions[self.last_encoder_state] == current_state
        ):
            direction = "CCW"
        else:
            # Invalid transition - possible encoder error or missed step
            self.encoder_errors += 1
            print(
                "WARNING: Invalid encoder transition: {} -> {}".format(
                    self.last_encoder_state, current_state
                )
            )
            direction = None

        self.last_encoder_state = current_state
        return direction

    def update_encoder_tracking(self):
        """
        Update encoder state tracking and calculate rotation speed with error detection
        Should be called regularly during movement operations
        """
        current_time = time.time()
        current_state = self.read_encoder_state()

        if current_state is None:
            self.encoder_errors += 1
            return False  # Error reading encoder

        # Detect direction from state transition
        direction = self.detect_encoder_direction(current_state)

        if direction is not None:
            self.encoder_direction = direction

            # Calculate rotation speed based on timing
            time_delta = current_time - self.last_encoder_time
            if time_delta > 0:
                # Each encoder transition represents 1/4 of encoder resolution
                # Speed calculation: (degrees per tick) / (time per transition)
                speed_deg_per_sec = (self.TICKS_TO_DEG / 4.0) / time_delta
                self.encoder_speed = speed_deg_per_sec

                # Track maximum observed rotation speed for optimization
                if speed_deg_per_sec > self.max_rotation_speed:
                    self.max_rotation_speed = speed_deg_per_sec

                # Detect unrealistic speed changes (possible encoder error)
                if hasattr(self, "last_encoder_speed") and self.last_encoder_speed > 0:
                    speed_change_ratio = speed_deg_per_sec / self.last_encoder_speed
                    if speed_change_ratio > 5.0 or speed_change_ratio < 0.2:
                        print(
                            "WARNING: Sudden encoder speed change: %.2f -> %.2f deg/s"
                            % (self.last_encoder_speed, speed_deg_per_sec)
                        )
                        self.encoder_errors += 1

                self.last_encoder_speed = speed_deg_per_sec

            # Update history for debugging (keep last 10 states)
            self.encoder_state_history.append(
                {
                    "time": current_time,
                    "state": current_state,
                    "direction": direction,
                    "speed": self.encoder_speed,
                }
            )
            if len(self.encoder_state_history) > 10:
                self.encoder_state_history.pop(0)
        else:
            # No valid direction detected - could be stopped or error
            if (
                self.last_encoder_state is not None
                and current_state != self.last_encoder_state
            ):
                # State changed but no valid direction - this is an error
                self.encoder_errors += 1

        self.last_encoder_time = current_time

        # Encoder error recovery: reset if too many errors
        if self.encoder_errors > self.encoder_error_threshold:
            print(
                "WARNING: Too many encoder errors (%d), resetting encoder tracking"
                % self.encoder_errors
            )
            self.reset_encoder_tracking()

        return True

    def reset_encoder_tracking(self):
        """
        Reset encoder tracking state - useful for error recovery
        """
        print("Resetting encoder tracking state...")
        self.encoder_state_history = []
        self.last_encoder_state = None
        self.encoder_direction = None
        self.encoder_errors = 0
        self.encoder_speed = 0.0
        self.last_encoder_time = time.time()
        if hasattr(self, "last_encoder_speed"):
            self.last_encoder_speed = 0.0

    def validate_encoder_direction(self, expected_direction):
        """
        Validate that encoder direction matches commanded motor direction

        Args:
            expected_direction: 'CW' or 'CCW' - the commanded direction

        Returns:
            True if directions match, False if mismatch detected
        """
        if self.encoder_direction is None:
            return None  # No encoder movement detected yet

        # Convert dome direction constants to strings for comparison
        if expected_direction == self.CW:
            expected_str = "CW"
        elif expected_direction == self.CCW:
            expected_str = "CCW"
        else:
            expected_str = str(expected_direction)

        direction_match = self.encoder_direction == expected_str

        if not direction_match:
            print(
                "WARNING: Direction mismatch! Commanded: {}, Encoder: {}".format(
                    expected_str, self.encoder_direction
                )
            )

        return direction_match

    def get_encoder_diagnostics(self):
        """
        Get encoder diagnostic information for troubleshooting

        Returns:
            dict: Encoder state, direction, speed, errors, and recent history
        """
        current_state = self.read_encoder_state()

        return {
            "current_state": current_state,
            "last_state": self.last_encoder_state,
            "direction": self.encoder_direction,
            "speed_deg_per_sec": self.encoder_speed,
            "max_speed_deg_per_sec": self.max_rotation_speed,
            "error_count": self.encoder_errors,
            "state_history": self.encoder_state_history[-5:],  # Last 5 states
            "encoder_pins": {"A": self.A, "B": self.B},
        }

    def get_home_polling_diagnostics(self):
        """
        Get home switch polling diagnostic information for optimization analysis

        Returns:
            dict: Polling rates, signal duration, validation settings, and timing data
        """
        return {
            "polling_rates": {
                "fast": self.home_poll_fast,
                "normal": self.home_poll_normal or self.POLL,
                "current": self.POLL,
            },
            "signal_validation": {
                "current_duration": self.home_signal_duration,
                "debounce_threshold": self.home_switch_debounce,
                "history_count": len(self.home_switch_history),
            },
            "speed_tracking": {
                "current_speed": self.encoder_speed,
                "max_observed_speed": self.max_rotation_speed,
            },
            "switch_history": self.home_switch_history[-5:],  # Last 5 readings
            "home_pin": self.HOME,
        }

    def calibrate_encoder_ticks_to_degrees(
        self, calibration_degrees=360.0, timeout=180.0
    ):
        """
        Calibrate encoder ticks-to-degrees ratio by performing a full rotation

        This method performs an automated calibration by:
        1. Starting from home position
        2. Rotating the dome a known amount (default 360 degrees)
        3. Counting encoder ticks during rotation
        4. Calculating the actual ticks-to-degrees ratio

        Args:
            calibration_degrees (float): Known rot amount for calib (default 360 deg)
            timeout (float): Maximum time to allow for calibration (default 180s)

        Returns:
            dict: Calibration results including measured ratio and accuracy
        """
        print("Starting encoder calibration...")

        # Ensure we're at home position first
        if not self.isHome():
            print("Moving to home position for calibration...")
            if not self.home():
                raise Exception("Failed to reach home position for calibration")

        # Reset encoder tracking
        self.encoder_state_history = []
        self.encoder_errors = 0

        print("Starting calibration rotation of %.1f degrees..." % calibration_degrees)
        calibration_start = time.time()

        # Start rotation (use CW direction for calibration)
        self.cw()
        if not self.start_rotation():
            raise Exception("Failed to start calibration rotation")

        # Track encoder transitions during rotation
        tick_count = 0
        last_encoder_state = self.read_encoder_state()

        try:
            while True:
                # Check timeout
                elapsed = time.time() - calibration_start
                if elapsed > timeout:
                    raise Exception("Calibration timeout after %.1f seconds" % elapsed)

                # Update encoder tracking
                current_state = self.read_encoder_state()
                if current_state != last_encoder_state and current_state is not None:
                    tick_count += 1
                    last_encoder_state = current_state

                    # Calculate current degrees based on tick count
                    if tick_count > 0:
                        current_degrees = (tick_count * calibration_degrees) / (
                            calibration_degrees / self.TICKS_TO_DEG
                        )
                        print(
                            "Calibration: %d ticks, est. %.1f degrees"
                            % (tick_count, current_degrees)
                        )

                # Check if we've completed the rotation (back to home)
                if (
                    elapsed > 10.0 and self.isHome()
                ):  # Give at least 10 seconds before checking home
                    print("Completed calibration rotation")
                    break

                time.sleep(0.02)  # Fast polling for accurate tick counting

        finally:
            # Always stop rotation
            self.stop_rotation()

        # Calculate calibration results
        total_time = time.time() - calibration_start
        measured_ticks_to_deg = (
            tick_count / calibration_degrees if calibration_degrees > 0 else 0
        )
        current_ticks_to_deg = self.TICKS_TO_DEG
        accuracy_percent = (
            (measured_ticks_to_deg / current_ticks_to_deg * 100)
            if current_ticks_to_deg > 0
            else 0
        )

        results = {
            "calibration_degrees": calibration_degrees,
            "total_ticks": tick_count,
            "calibration_time": total_time,
            "current_ticks_to_deg": current_ticks_to_deg,
            "measured_ticks_to_deg": measured_ticks_to_deg,
            "accuracy_percent": accuracy_percent,
            "recommended_config": measured_ticks_to_deg,
            "encoder_errors": self.encoder_errors,
        }

        print("Encoder Calibration Results:")
        print("  Degrees rotated: %.1f" % calibration_degrees)
        print("  Total ticks counted: %d" % tick_count)
        print("  Current config: %.3f ticks/degree" % current_ticks_to_deg)
        print("  Measured ratio: %.3f ticks/degree" % measured_ticks_to_deg)
        print("  Accuracy: %.1f%%" % accuracy_percent)
        print("  Calibration time: %.1f seconds" % total_time)

        if abs(accuracy_percent - 100.0) > 10.0:
            print("WARNING: Calibration accuracy is outside 10% tolerance")
            print(
                "Consider updating dome_config.json with recommended value: %.3f"
                % measured_ticks_to_deg
            )

        return results

    def validate_encoder_consistency(self, test_duration=30.0):
        """
        Validate encoder A/B phase relationship and signal consistency

        This method checks for:
        - Proper Gray Code state transitions
        - A and B phase relationship (90-degree phase shift)
        - Signal noise and consistency
        - Invalid state transitions

        Args:
            test_duration (float): Test duration in seconds (default 30s)

        Returns:
            dict: Validation results and detected issues
        """
        print("Starting encoder consistency validation...")

        # Reset tracking variables
        self.encoder_errors = 0
        self.encoder_state_history = []

        validation_start = time.time()
        state_counts = {
            0: 0,
            1: 0,
            2: 0,
            3: 0,
        }  # Count occurrences of each Gray Code state
        transition_counts = {}  # Count state transitions
        invalid_transitions = 0

        print("Collecting encoder data for %.1f seconds..." % test_duration)

        last_state = None
        while time.time() - validation_start < test_duration:
            current_state = self.read_encoder_state()

            if current_state is not None:
                state_counts[current_state] += 1

                if last_state is not None and current_state != last_state:
                    # Record transition
                    transition_key = "%d->%d" % (last_state, current_state)
                    transition_counts[transition_key] = (
                        transition_counts.get(transition_key, 0) + 1
                    )

                    # Check for valid Gray Code transition
                    valid_transitions = {
                        0: [1, 2],  # 00 can go to 01 or 10
                        1: [0, 3],  # 01 can go to 00 or 11
                        2: [0, 3],  # 10 can go to 00 or 11
                        3: [1, 2],  # 11 can go to 01 or 10
                    }

                    if current_state not in valid_transitions.get(last_state, []):
                        invalid_transitions += 1
                        print("Invalid transition detected: %s" % transition_key)

                last_state = current_state

            time.sleep(0.01)  # 100Hz sampling

        # Analyze results
        total_samples = sum(state_counts.values())
        total_transitions = sum(transition_counts.values())

        # Check for balanced state distrib (each state should appear roughly equally)
        expected_per_state = total_samples / 4.0
        state_balance = {}
        for state, count in state_counts.items():
            percentage = (count / total_samples * 100) if total_samples > 0 else 0
            deviation = (
                abs(count - expected_per_state) / expected_per_state * 100
                if expected_per_state > 0
                else 0
            )
            state_balance[state] = {
                "count": count,
                "percentage": percentage,
                "deviation": deviation,
            }

        # Check for missing states or excessive imbalance
        missing_states = [
            state for state, data in state_balance.items() if data["count"] == 0
        ]
        imbalanced_states = [
            state for state, data in state_balance.items() if data["deviation"] > 50.0
        ]

        results = {
            "test_duration": test_duration,
            "total_samples": total_samples,
            "state_counts": state_counts,
            "state_balance": state_balance,
            "transition_counts": transition_counts,
            "total_transitions": total_transitions,
            "invalid_transitions": invalid_transitions,
            "missing_states": missing_states,
            "imbalanced_states": imbalanced_states,
            "encoder_errors": self.encoder_errors,
            "validation_passed": len(missing_states) == 0
            and len(imbalanced_states) == 0
            and invalid_transitions == 0,
        }

        print("Encoder Consistency Validation Results:")
        print("  Total samples: %d" % total_samples)
        print("  Total transitions: %d" % total_transitions)
        print("  Invalid transitions: %d" % invalid_transitions)
        print("  Missing states: %s" % (missing_states if missing_states else "None"))
        print("  State distribution:")
        for state, data in state_balance.items():
            print(
                "    State %d: %d samples (%.1f%%, deviation %.1f%%)"
                % (state, data["count"], data["percentage"], data["deviation"])
            )

        if results["validation_passed"]:
            print("OK Encoder consistency validation PASSED")
        else:
            print("X Encoder consistency validation FAILED")
            if missing_states:
                print("  Issue: Missing encoder states - check wiring")
            if imbalanced_states:
                print("  Issue: Unbalanced state distribution - check for noise")
            if invalid_transitions > 0:
                print("  Issue: Invalid Gray Code transitions - check signal quality")

        return results

    def get_encoder_calibration_status(self):
        """
        Get current encoder calibration status and recommendations

        Returns:
            dict: Current configuration, estimated accuracy, and recommendations
        """
        return {
            "current_config": {
                "ticks_to_degrees": self.TICKS_TO_DEG,
                "encoder_pins": {"A": self.A, "B": self.B},
            },
            "performance": {
                "current_speed": self.encoder_speed,
                "max_observed_speed": self.max_rotation_speed,
                "error_count": self.encoder_errors,
            },
            "recommendations": {
                "calibration_needed": self.max_rotation_speed
                == 0.0,  # No movement detected
                "consistency_check_needed": self.encoder_errors > 0,
                "recalibration_suggested": False,  # Could add logic based on error rate
            },
        }

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

    def is_home_with_validation(self):
        """
        Enhanced home switch detection with signal validation and debouncing.

        This method provides optimized home switch detection for reliable operation
        at maximum rotation speeds. It includes:
        - Signal duration measurement and debouncing
        - History tracking for noise rejection
        - Timing analysis for debugging

        Returns:
            bool: True if home switch is reliably detected
        """
        try:
            current_time = time.time()
            home_switch_active = self.dome.digital_in(self.HOME)

            # Track home switch history for debouncing
            self.home_switch_history.append(
                {
                    "time": current_time,
                    "state": home_switch_active,
                    "poll_rate": self.POLL,
                }
            )

            # Keep only recent history (last 2 seconds)
            cutoff_time = current_time - 2.0
            self.home_switch_history = [
                h for h in self.home_switch_history if h["time"] >= cutoff_time
            ]

            if home_switch_active:
                # Home switch is currently active
                # Find start of current signal
                signal_start = None
                for i in range(len(self.home_switch_history) - 1, -1, -1):
                    if self.home_switch_history[i]["state"]:
                        signal_start = self.home_switch_history[i]["time"]
                    else:
                        break

                if signal_start is not None:
                    self.home_signal_duration = current_time - signal_start

                    # Check if signal duration meets debounce requirement
                    if self.home_signal_duration >= self.home_switch_debounce:
                        print(
                            "Home switch validated: signal duration %.3fs (min %.3fs)"
                            % (self.home_signal_duration, self.home_switch_debounce)
                        )
                        self.is_home = True
                        return True
                    else:
                        # Signal too short, keep polling
                        return False
                else:
                    # Just started, reset duration
                    self.home_signal_duration = 0.0
                    return False
            else:
                # Home switch not active
                self.home_signal_duration = 0.0
                self.is_home = False
                return False

        except Exception as e:
            raise Exception("Hardware error in enhanced home detection: {}".format(e))

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
        Stop dome rotation (emergency stop) - Legacy method
        Uses new stop_rotation() for consistent behavior
        """
        return self.stop_rotation()

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
