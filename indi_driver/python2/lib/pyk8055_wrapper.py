"""
K8055 Mock/Wrapper for INDI Dome Driver

A Python module that provides libk8055-compatible interface for dome operations.
Can run in mock mode for testing or connect to actual hardware.

Copyright 2025 Observatory Developer
Free software. Do what you want with it.
"""


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
        self.debug = True
        self.mock = False
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
            print(
                "K8055 {} device initialized at address {}".format(
                    mode_text, BoardAddress
                )
            )

        # Auto-open device
        try:
            self.OpenDevice(BoardAddress)
        except Exception:
            if not mock:
                raise K8055Error("Could not open device - hardware not available")

    def _log(self, message):
        """Log debug message if debug is enabled"""
        # if self.debug:
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
            self._log(
                "Attempting to connect to hardware at address {}".format(BoardAddress)
            )
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
                    raise K8055Error("Hardware mode requires 'pyk8055' module.")
                except Exception as hw_error:
                    self._log("Hardware connection failed: {}".format(hw_error))
                    raise K8055Error(
                        "Hardware device connection failed: {}\n"
                        "Check:\n"
                        "  - K8055 board is connected via USB\n"
                        "  - Board address {} is correct (0-3)\n"
                        "  - USB permissions (may need sudo or udev rules)\n"
                        "  - No other applications using the device".format(
                            hw_error, BoardAddress
                        )
                    )

            except (ImportError, Exception) as e:
                self._log("Hardware connection failed: {}".format(e))
                raise K8055Error(
                    "Could not open hardware device at address {}: {}".format(
                        BoardAddress, e
                    )
                )


# Compatibility wrapper class for existing dome.py code
class device:
    """
    Compatibility wrapper that maintains the old interface
    while using the new libk8055-style k8055 class internally
    """

    def __init__(self, port=0, mock=True):
        """Initialize device wrapper"""
        self.k8055_device = k8055(
            BoardAddress=port, debug=False, mock=mock
        )._hardware_device

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

    def read_all_digital(self):
        """Read all digital inputs as bitmask (wrapper interface)"""
        return self.k8055_device.ReadAllDigital()
