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

        # Set some realistic mock values for dome operations
        self._analog_inputs[1] = 50  # Shutter upper limit
        self._analog_inputs[2] = 200  # Shutter lower limit

        if self.debug:
            mode_text = "mock" if mock else "hardware"
            print(f"K8055 {mode_text} device initialized at address {BoardAddress}")

        # Auto-open device
        try:
            self.OpenDevice(BoardAddress)
        except Exception:
            if not mock:
                raise K8055Error("Could not open device - hardware not available")

    def _log(self, message):
        """Log debug message if debug is enabled"""
        if self.debug:
            print(f"K8055[{self.BoardAddress}]: {message}")

    def OpenDevice(self, BoardAddress):
        """
        Open connection to K8055 device

        Returns:
            0 if successful, raises K8055Error if failed
        """
        self.BoardAddress = BoardAddress
        if self.mock:
            self._log(f"Opening mock device at address {BoardAddress}")
            self.is_open = True
            return 0
        else:
            # In production mode, try to connect to real hardware
            self._log(f"Attempting to connect to hardware at address {BoardAddress}")
            try:
                # This is where real libk8055 integration would go
                # For now, we simulate hardware not being available

                # Try to import and use real libk8055
                # import pyk8055  # This would be the real SWIG-generated module
                # self._hardware_device = pyk8055.k8055(BoardAddress)
                # self.is_open = True
                # return 0

                # Since we don't have real hardware, raise error
                raise K8055Error(
                    "Hardware mode not implemented - no libk8055 available"
                )

            except (ImportError, Exception) as e:
                self._log(f"Hardware connection failed: {e}")
                raise K8055Error(
                    f"Could not open hardware device at address {BoardAddress}: {e}"
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
        self._log(f"Setting digital channel {Channel} ON")
        self._digital_outputs[Channel] = True
        return 0

    def ClearDigitalChannel(self, Channel):
        """Set digital output channel (1-8) to LOW"""
        if not (1 <= Channel <= 8):
            return -1
        self._log(f"Setting digital channel {Channel} OFF")
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

        # Mock some realistic behavior for dome sensors
        if Channel == 3:  # Home switch
            # Simulate home switch being triggered occasionally
            result = int(time.time() % 30 < 2)  # Trigger for 2 seconds every 30
        else:
            result = int(self._digital_inputs[Channel])

        self._log(f"Reading digital channel {Channel}: {result}")
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
        self._log(f"Reading analog channel {Channel}: {value}")
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
        self._log(f"Reading counter {CounterNo}: {value}")
        return value

    def ResetCounter(self, CounterNo):
        """Reset counter (1-2) to zero"""
        if not (1 <= CounterNo <= 2):
            return -1
        self._log(f"Resetting counter {CounterNo}")
        self._counters[CounterNo] = 0
        return 0

    def SetCounterDebounceTime(self, CounterNo, DebounceTime):
        """Set counter debounce time (1-7450 ms)"""
        if not (1 <= CounterNo <= 2) or not (0 <= DebounceTime <= 7450):
            return -1
        self._log(f"Setting counter {CounterNo} debounce to {DebounceTime}ms")
        self._counter_debounce[CounterNo] = DebounceTime
        return 0

    # Additional functions for compatibility

    def WriteAllDigital(self, data):
        """Write bitmask to all digital outputs"""
        self._log(f"Writing digital bitmask: {data}")
        for i in range(1, 9):
            self._digital_outputs[i] = bool(data & (1 << (i - 1)))
        return 0

    def ReadAllDigital(self):
        """Read all digital inputs as bitmask"""
        value = 0
        for i in range(1, 6):
            if self._digital_inputs[i]:
                value |= 1 << (i - 1)
        self._log(f"Reading all digital inputs: {value}")
        return value

    def OutputAnalogChannel(self, Channel, data):
        """Set analog output channel (1-2) value"""
        if not (1 <= Channel <= 2) or not (0 <= data <= 255):
            return -1
        self._log(f"Setting analog channel {Channel} to {data}")
        self._analog_outputs[Channel] = data
        return 0

    def ReadAllAnalog(self):
        """Read both analog input channels"""
        data1 = self._analog_inputs[1]
        data2 = self._analog_inputs[2]
        self._log(f"Reading all analog inputs: {data1}, {data2}")
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
