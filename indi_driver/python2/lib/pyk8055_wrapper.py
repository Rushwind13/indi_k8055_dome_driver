"""
K8055 Mock/Wrapper for INDI Dome Driver

A Python module that provides libk8055-compatible interface for dome operations.
Can run in mock mode for testing or connect to actual hardware.

Copyright 2025 Observatory Developer
Free software. Do what you want with it.
"""

import time


class K8055Error(Exception):
    """Exception raised for K8055 hardware errors"""

    pass


class k8055:
    """
    Mock K8055 device class that mimics libk8055 interface
    for dome operations. Provides testable mock functionality.
    """

    def __init__(self, BoardAddress=0, debug=False, mock=True):
        """
        Initialize K8055 device

        Args:
            BoardAddress: K8055 board address (0-3)
            debug: Enable debug output
            mock: Run in mock mode (True) or try to connect to hardware (False)
        """
        self.BoardAddress = BoardAddress
        self.debug = debug
        self.mock = mock
        self.is_open = False

        # Mock hardware state
        self._digital_outputs = [False] * 9  # Channels 1-8 (index 0 unused)
        self._digital_inputs = [False] * 6  # Channels 1-5 (index 0 unused)
        self._analog_outputs = [0, 0, 0]  # Channels 1-2 (index 0 unused)
        self._analog_inputs = [0, 0, 0]  # Channels 1-2 (index 0 unused)
        self._counters = [0, 0, 0]  # Counters 1-2 (index 0 unused)
        self._counter_debounce = [0, 0, 0]  # Debounce times

        # Hardware device reference (set in OpenDevice if hardware mode)
        self._hardware_device = None

        # Set some realistic mock values for dome operations
        self._analog_inputs[1] = 50  # Shutter upper limit
        self._analog_inputs[2] = 200  # Shutter lower limit

        if self.debug:
            mode_text = "mock" if mock else "hardware"
            print("K8055 {} device initialized at address {}".format(mode_text, BoardAddress))

        # Auto-open device
        try:
            self.OpenDevice(BoardAddress)
        except Exception:
            if not mock:
                raise K8055Error("Could not open device - hardware not available")

    def _log(self, message):
        """Log debug message if debug is enabled"""
        if self.debug:
            print("K8055[{}]: {}".format(self.BoardAddress, message))

    def OpenDevice(self, BoardAddress):
        """
        Open connection to K8055 device

        Returns:
            0 if successful, raises K8055Error if failed
        """
        self.BoardAddress = BoardAddress
        if self.mock:
            self._log("Opening mock device at address {}".format(BoardAddress))
            self.is_open = True
            return 0
        else:
            # In production mode, try to connect to real hardware
            self._log("Attempting to connect to hardware at address {}".format(BoardAddress))
            try:
                # Try to import real libk8055 hardware interface
                try:
                    import pyk8055  # Real SWIG-generated K8055 module

                    self._log(
                        "Found real pyk8055 module - attempting hardware connection"
                    )

                    # Create hardware device instance
                    self._hardware_device = pyk8055.k8055(BoardAddress)

                    # Test basic connectivity
                    if (
                        hasattr(self._hardware_device, "IsOpen")
                        and self._hardware_device.IsOpen()
                    ):
                        self._log("Hardware device opened successfully")
                        self.is_open = True
                        return 0
                    else:
                        # Try to open the device
                        if hasattr(self._hardware_device, "OpenDevice"):
                            result = self._hardware_device.OpenDevice(BoardAddress)
                            if result == 0:
                                self._log("Hardware device opened via OpenDevice()")
                                self.is_open = True
                                return 0
                            else:
                                raise K8055Error(
                                    "Hardware OpenDevice() returned {}".format(result)
                                )
                        else:
                            # Assume device is ready if it instantiated
                            self._log("Hardware device instantiated - assuming ready")
                            self.is_open = True
                            return 0

                except ImportError:
                    self._log("pyk8055 module not found - hardware not available")
                    raise K8055Error(
                        "Hardware mode requires 'pyk8055' module. Install with:\n"
                        "  sudo apt-get install libk8055-dev python3-dev\n"
                        "  pip install pyk8055\n"
                        "Or build from source: https://github.com/rm-hull/pyk8055"
                    )
                except Exception as hw_error:
                    self._log("Hardware connection failed: {}".format(hw_error))
                    raise K8055Error(
                        "Hardware device connection failed: {}\n"
                        "Check:\n"
                        "  - K8055 board is connected via USB\n"
                        "  - Board address {} is correct (0-3)\n"
                        "  - USB permissions (may need sudo or udev rules)\n"
                        "  - No other applications using the device".format(hw_error, BoardAddress)
                    )

            except (ImportError, Exception) as e:
                self._log("Hardware connection failed: {}".format(e))
                raise K8055Error(
                    "Could not open hardware device at address {}: {}".format(BoardAddress, e)
                )

    def CloseDevice(self):
        """Close connection to K8055 device"""
        self._log("Closing device")
        self.is_open = False
        return 0

    # Digital I/O Functions (Required for dome operations)

    def SetDigitalChannel(self, Channel):
        """Set digital output channel (1-8) to HIGH"""
        if not (1 <= Channel <= 8):
            return -1

        self._log("Setting digital channel {} ON".format(Channel))

        # Use hardware device if available
        if self._hardware_device and not self.mock:
            try:
                result = self._hardware_device.SetDigitalChannel(Channel)
                self._digital_outputs[
                    Channel
                ] = True  # Update mock state for consistency
                return result
            except Exception as e:
                self._log("Hardware SetDigitalChannel failed: {}".format(e))
                raise K8055Error("Hardware SetDigitalChannel failed: {}".format(e))
        else:
            # Mock mode
            self._digital_outputs[Channel] = True
            return 0

    def ClearDigitalChannel(self, Channel):
        """Set digital output channel (1-8) to LOW"""
        if not (1 <= Channel <= 8):
            return -1

        self._log("Setting digital channel {} OFF".format(Channel))

        # Use hardware device if available
        if self._hardware_device and not self.mock:
            try:
                result = self._hardware_device.ClearDigitalChannel(Channel)
                self._digital_outputs[
                    Channel
                ] = False  # Update mock state for consistency
                return result
            except Exception as e:
                self._log("Hardware ClearDigitalChannel failed: {}".format(e))
                raise K8055Error("Hardware ClearDigitalChannel failed: {}".format(e))
        else:
            # Mock mode
            self._digital_outputs[Channel] = False
            return 0

    def ReadDigitalChannel(self, Channel):
        """
        Read digital input channel (1-5)

        Returns:
            1 if HIGH, 0 if LOW, -1 on error
        """
        if not self.is_open:
            raise K8055Error("Device not open")

        if not (1 <= Channel <= 5):
            return -1

        # Use hardware device if available
        if self._hardware_device and not self.mock:
            try:
                result = self._hardware_device.ReadDigitalChannel(Channel)
                self._log("Reading digital channel {} (hardware): {}".format(Channel, result))
                return result
            except Exception as e:
                self._log("Hardware ReadDigitalChannel failed: {}".format(e))
                raise K8055Error("Hardware ReadDigitalChannel failed: {}".format(e))
        else:
            # Mock some realistic behavior for dome sensors
            if Channel == 3:  # Home switch
                # If explicitly set in digital inputs, use that value
                if self._digital_inputs[Channel]:
                    result = 1
                else:
                    # Simulate home switch being triggered occasionally when not set
                    result = int(time.time() % 30 < 2)  # Trigger for 2s every 30s
            else:
                result = int(self._digital_inputs[Channel])

            self._log("Reading digital channel {} (mock): {}".format(Channel, result))
            return result

    # Analog I/O Functions (Required for shutter limits)

    def ReadAnalogChannel(self, Channel):
        """
        Read analog input channel (1-2)

        Returns:
            Value 0-255, -1 on error
        """
        if not (1 <= Channel <= 2):
            return -1

        value = self._analog_inputs[Channel]
        self._log("Reading analog channel {}: {}".format(Channel, value))
        return value

    # Counter Functions (Required for encoder position)

    def ReadCounter(self, CounterNo):
        """
        Read counter value (1-2)

        Returns:
            Counter value, -1 on error
        """
        if not (1 <= CounterNo <= 2):
            return -1

        # Simulate encoder ticks incrementing during rotation
        if self._digital_outputs[1]:  # If dome rotation is on
            self._counters[CounterNo] += 1

        value = self._counters[CounterNo]
        self._log("Reading counter {}: {}".format(CounterNo, value))
        return value

    def ResetCounter(self, CounterNo):
        """Reset counter (1-2) to zero"""
        if not (1 <= CounterNo <= 2):
            return -1
        self._log("Resetting counter {}".format(CounterNo))
        self._counters[CounterNo] = 0
        return 0

    def SetCounterDebounceTime(self, CounterNo, DebounceTime):
        """Set counter debounce time (1-7450 ms)"""
        if not (1 <= CounterNo <= 2) or not (0 <= DebounceTime <= 7450):
            return -1
        self._log("Setting counter {} debounce to {}ms".format(CounterNo, DebounceTime))
        self._counter_debounce[CounterNo] = DebounceTime
        return 0

    # Additional functions for compatibility

    def WriteAllDigital(self, data):
        """Write bitmask to all digital outputs"""
        self._log("Writing digital bitmask: {}".format(data))
        for i in range(1, 9):
            self._digital_outputs[i] = bool(data & (1 << (i - 1)))
        return 0

    def ReadAllDigital(self):
        """Read all digital inputs as bitmask"""
        value = 0
        for i in range(1, 6):
            if self._digital_inputs[i]:
                value |= 1 << (i - 1)
        self._log("Reading all digital inputs: {}".format(value))
        return value

    def OutputAnalogChannel(self, Channel, data):
        """Set analog output channel (1-2) value"""
        if not (1 <= Channel <= 2) or not (0 <= data <= 255):
            return -1
        self._log("Setting analog channel {} to {}".format(Channel, data))
        self._analog_outputs[Channel] = data
        return 0

    def ReadAllAnalog(self):
        """Read both analog input channels"""
        data1 = self._analog_inputs[1]
        data2 = self._analog_inputs[2]
        self._log("Reading all analog inputs: {}, {}".format(data1, data2))
        return [0, data1, data2]  # Return format matches libk8055

    def IsOpen(self):
        """Check if device is open"""
        return self.is_open

    def DeviceAddress(self):
        """Get device address"""
        return self.BoardAddress


# Compatibility wrapper class for existing dome.py code
class device:
    """
    Compatibility wrapper that maintains the old interface
    while using the new libk8055-style k8055 class internally
    """

    def __init__(self, port=0, mock=True):
        """Initialize device wrapper"""
        self.k8055_device = k8055(BoardAddress=port, debug=False, mock=mock)

    # Map old method names to new libk8055-style names

    def digital_on(self, channel):
        """Turn digital channel ON (old interface)"""
        return self.k8055_device.SetDigitalChannel(channel)

    def digital_off(self, channel):
        """Turn digital channel OFF (old interface)"""
        return self.k8055_device.ClearDigitalChannel(channel)

    def digital_in(self, channel):
        """Read digital input channel (old interface)"""
        return self.k8055_device.ReadDigitalChannel(channel)

    def analog_in(self, channel):
        """Read analog input channel (old interface)"""
        return self.k8055_device.ReadAnalogChannel(channel)

    def counter_read(self, channel):
        """Read counter value (old interface)"""
        return self.k8055_device.ReadCounter(channel)

    def counter_reset(self, channel):
        """Reset counter (old interface)"""
        return self.k8055_device.ResetCounter(channel)

    def counter_set_debounce(self, channel, time):
        """Set counter debounce time (old interface)"""
        return self.k8055_device.SetCounterDebounceTime(channel, time)
