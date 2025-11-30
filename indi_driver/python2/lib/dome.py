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
        self.DEG_TO_TICKS = self.config["calibration"].get(
            "degrees_to_ticks", 1.0
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
        # NOTE: Encoder reset removed - hardware counter is absolute value (always counts up)
        # Resetting here causes position errors because we lose accumulated ticks
        # Encoder should only reset when crossing home position
        # self.encoder_reset()
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
                    self.set_pos(self.HOME_POS, reset_encoder=True)
                    break
                time.sleep(self.POLL)
        else:
            print("Rotating to azimuth {:.1f}...".format(azimuth))
            sys.stdout.flush()
            encoder_ticks = 0
            target_ticks = round(distance * self.DEG_TO_TICKS)
            while encoder_ticks < target_ticks:
                encoder_ticks, _ = self.counter_read()
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
        if self.isHome():
            # Reset encoder when at home position
            self.set_pos(self.HOME_POS, reset_encoder=True)
            return
        encoder_ticks, _ = self.counter_read()
        # Hardware counter is absolute (always counts up regardless of direction)
        # Direction is applied by motor wiring, not by software calculation
        change_in_pos = (encoder_ticks / self.DEG_TO_TICKS) % 360.0
        # Always ADD ticks - CW adds forward, CCW adds backward (motor direction handles sign)
        if self.dir == self.CW:
            new_pos = (self.get_pos() + change_in_pos) % 360.0
        else:
            # CCW: motor moves backwards, but counter still counts up
            new_pos = (self.get_pos() - change_in_pos) % 360.0
        self.set_pos(new_pos)

    def current_pos(self):
        orig_pos = self.get_pos()
        encoder_ticks, _ = self.counter_read()
        # Hardware counter is absolute (always counts up regardless of direction)
        change_in_pos = (encoder_ticks / self.DEG_TO_TICKS) % 360.0
        if self.dir == self.CW:
            new_pos = (orig_pos + change_in_pos) % 360.0
        else:
            # CCW: motor moves backwards, but counter still counts up
            new_pos = (orig_pos - change_in_pos) % 360.0
        return new_pos

    # Reset the tick counters to 0 when you reach target position
    def set_pos(self, in_pos, reset_encoder=False):
        encoder_ticks, _ = self.counter_read()
        print(
            "Encoder ticks: {}, Updated position: {:.1f}".format(encoder_ticks, in_pos)
        )
        # Only reset encoder when explicitly requested (e.g., at home position)
        if reset_encoder:
            self.encoder_reset()
        self.position = in_pos

    def encoder_reset(self):
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
            return self.direction_str()  # No change

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
                speed_deg_per_sec = (self.DEG_TO_TICKS / 4.0) / time_delta
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

    def calibrate_encoder_degrees_to_ticks(
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
                            calibration_degrees / self.DEG_TO_TICKS
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
        current_ticks_to_deg = self.DEG_TO_TICKS
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
                "degrees_to_ticks": self.DEG_TO_TICKS,
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
