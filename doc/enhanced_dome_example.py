#!/usr/bin/env python3
"""
Enhanced Dome Initialization with Hardware Detection and Fallback

This shows how to modify dome.py to automatically handle both hardware
and mock modes with graceful fallback.
"""

import os
import platform
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pyk8055_wrapper
from config import load_config


class EnhancedDome:
    """
    Enhanced dome class with automatic hardware detection and fallback.

    This version can:
    1. Automatically detect the environment (Mac vs Raspberry Pi)
    2. Try hardware mode first, fall back to mock if needed
    3. Provide clear feedback about which mode is active
    4. Handle configuration appropriately for each mode
    """

    def __init__(self, config_file="dome_config.json"):
        print("Creating Enhanced Dome object with hardware detection...")
        sys.stdout.flush()

        # Load configuration
        if isinstance(config_file, dict):
            self.config = config_file
        else:
            self.config = load_config(config_file)

        # Initialize hardware interface with smart detection
        self._initialize_hardware()

        # Load the rest of the configuration
        self._load_pin_configuration()
        self._load_calibration_settings()
        self._initialize_dome_state()

        print("Enhanced Dome initialization complete.")
        sys.stdout.flush()

    def _initialize_hardware(self):
        """Initialize hardware with automatic detection and fallback."""
        device_port = self.config["hardware"]["device_port"]

        # Check configuration preference
        config_mock_mode = self.config["hardware"].get("mock_mode", None)

        if config_mock_mode is True:
            # Configuration explicitly requests mock mode
            print("Configuration specifies mock mode - using simulation")
            self.hardware_mode = "mock_explicit"
            self.dome = pyk8055_wrapper.device(port=device_port, mock=True)

        elif config_mock_mode is False:
            # Configuration explicitly requests hardware mode
            print(
                "Configuration specifies hardware mode - attempting real connection..."
            )
            try:
                self.dome = pyk8055_wrapper.device(port=device_port, mock=False)
                self.hardware_mode = "hardware"
                print("✅ Connected to real K8055 hardware")

            except pyk8055_wrapper.K8055Error as e:
                print(f"❌ Hardware connection failed: {e}")
                print("🔄 Falling back to mock mode for safety...")
                self.dome = pyk8055_wrapper.device(port=device_port, mock=True)
                self.hardware_mode = "mock_fallback"

        else:
            # No explicit configuration - use environment detection
            print("No mock_mode specified - detecting environment...")
            auto_mock_mode = self._detect_environment()

            if auto_mock_mode:
                print("Environment detection: Development system - using mock mode")
                self.hardware_mode = "mock_auto"
                self.dome = pyk8055_wrapper.device(port=device_port, mock=True)
            else:
                print(
                    "Environment detection: Production system - attempting hardware connection..."
                )
                try:
                    self.dome = pyk8055_wrapper.device(port=device_port, mock=False)
                    self.hardware_mode = "hardware"
                    print("✅ Connected to real K8055 hardware")

                except pyk8055_wrapper.K8055Error as e:
                    print(f"❌ Hardware connection failed: {e}")
                    print("🔄 Falling back to mock mode...")
                    self.dome = pyk8055_wrapper.device(port=device_port, mock=True)
                    self.hardware_mode = "mock_fallback"

    def _detect_environment(self):
        """
        Detect if we're in a development or production environment.

        Returns:
            bool: True if mock mode recommended, False if hardware expected
        """
        # Check platform
        system = platform.system()

        # macOS/Windows are typically development
        if system in ["Darwin", "Windows"]:
            return True

        # Linux might be production, but check further
        if system == "Linux":
            # Check if we're on Raspberry Pi
            try:
                with open("/proc/cpuinfo", "r") as f:
                    if "Raspberry Pi" in f.read():
                        return False  # Raspberry Pi = production
            except:
                pass

            # Check if libk8055 is available
            try:
                # This would check for actual libk8055 installation
                import importlib.util

                spec = importlib.util.find_spec("pyk8055")
                if spec is not None:
                    return False  # libk8055 available = production
            except:
                pass

        # Default to mock mode for safety
        return True

    def _load_pin_configuration(self):
        """Load pin assignments from configuration."""
        self.A = self.config["pins"]["encoder_a"]
        self.B = self.config["pins"]["encoder_b"]
        self.HOME = self.config["pins"]["home_switch"]
        self.UPPER = self.config["pins"]["shutter_upper_limit"]
        self.LOWER = self.config["pins"]["shutter_lower_limit"]
        self.DOME_ROTATE = self.config["pins"]["dome_rotate"]
        self.DOME_DIR = self.config["pins"]["dome_direction"]
        self.SHUTTER_MOVE = self.config["pins"]["shutter_move"]
        self.SHUTTER_DIR = self.config["pins"]["shutter_direction"]

    def _load_calibration_settings(self):
        """Load calibration settings with mode-specific adjustments."""
        self.POLL = self.config["calibration"]["poll_interval"]
        self.HOME_POS = self.config["calibration"]["home_position"]
        self.TICKS_TO_DEG = self.config["calibration"]["ticks_to_degrees"]

        # Adjust timeouts based on hardware mode
        if self.hardware_mode.startswith("mock"):
            # Use faster timeouts for mock mode
            self.MAX_OPEN_TIME = self.config.get("testing", {}).get(
                "smoke_test_timeout", 3.0
            )
            print(f"Mock mode: Using fast timeout of {self.MAX_OPEN_TIME}s")
        else:
            # Use full timeouts for hardware mode
            self.MAX_OPEN_TIME = 30.0
            print(f"Hardware mode: Using full timeout of {self.MAX_OPEN_TIME}s")

    def _initialize_dome_state(self):
        """Initialize dome state variables."""
        self.CW = False
        self.CCW = True
        self.is_home = False
        self.is_turning = False
        self.dir = self.CW
        self.is_open = False
        self.is_closed = True
        self.is_opening = False
        self.is_closing = False
        self.position = 0.0

    def get_hardware_status(self):
        """Get detailed information about hardware mode and status."""
        return {
            "mode": self.hardware_mode,
            "description": {
                "hardware": "Connected to real K8055 hardware",
                "mock_explicit": "Mock mode explicitly configured",
                "mock_auto": "Mock mode automatically selected",
                "mock_fallback": "Mock mode - hardware connection failed",
            }[self.hardware_mode],
            "is_mock": self.hardware_mode.startswith("mock"),
            "is_hardware": self.hardware_mode == "hardware",
            "can_control_real_dome": self.hardware_mode == "hardware",
        }

    def print_status(self):
        """Print current dome and hardware status."""
        status = self.get_hardware_status()
        print("\n" + "=" * 50)
        print("🔭 DOME STATUS")
        print("=" * 50)
        print(f"Hardware Mode: {status['mode']}")
        print(f"Description: {status['description']}")
        print(f"Real Hardware: {'✅ Yes' if status['is_hardware'] else '❌ No (Mock)'}")
        print(f"Position: {self.get_pos():.1f}°")
        print(f"At Home: {'✅ Yes' if self.isHome() else '❌ No'}")
        print(f"Shutter Open: {'✅ Yes' if self.isOpen() else '❌ No'}")
        print("=" * 50)

    # Include all the original dome methods here
    # (For brevity, I'll just include a few key ones)

    def get_pos(self):
        """Get current dome position."""
        curr_ticks = self.dome.counter_read(self.A)
        self.position = curr_ticks * self.TICKS_TO_DEG
        return self.position

    def isHome(self):
        """Check if dome is at home position."""
        return self.is_home

    def isOpen(self):
        """Check if shutter is open."""
        return self.is_open

    def isClosed(self):
        """Check if shutter is closed."""
        return self.is_closed


def demonstrate_configuration_scenarios():
    """Demonstrate different configuration scenarios."""
    print("🔧 CONFIGURATION SCENARIOS DEMONSTRATION")
    print("=" * 60)

    # Scenario 1: Explicit mock mode (development)
    print("\n1. EXPLICIT MOCK MODE (Development)")
    print("-" * 40)
    mock_config = {
        "hardware": {"mock_mode": True, "device_port": 0},
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
            "poll_interval": 0.1,
            "home_position": 0.0,
            "ticks_to_degrees": 1.0,
        },
        "testing": {"smoke_test_timeout": 2.0},
    }

    dome1 = EnhancedDome(mock_config)
    dome1.print_status()

    # Scenario 2: Explicit hardware mode (will fall back to mock)
    print("\n2. EXPLICIT HARDWARE MODE (Production - with fallback)")
    print("-" * 40)
    hardware_config = mock_config.copy()
    hardware_config["hardware"]["mock_mode"] = False

    dome2 = EnhancedDome(hardware_config)
    dome2.print_status()

    # Scenario 3: Auto-detection mode
    print("\n3. AUTO-DETECTION MODE")
    print("-" * 40)
    auto_config = mock_config.copy()
    del auto_config["hardware"]["mock_mode"]  # Remove explicit setting

    dome3 = EnhancedDome(auto_config)
    dome3.print_status()


def create_deployment_guide():
    """Create a deployment guide for different environments."""
    guide = """
🚀 DEPLOYMENT GUIDE: Mock vs Hardware Modes
==========================================

DEVELOPMENT ENVIRONMENT (Mac/Windows):
--------------------------------------
1. Use dome_config_development.json:
   {
     "hardware": {"mock_mode": true, "device_port": 0},
     "testing": {"smoke_test": true, "smoke_test_timeout": 3.0}
   }

2. Or let auto-detection handle it (recommended):
   {
     "hardware": {"device_port": 0}
     // mock_mode not specified = auto-detect
   }

PRODUCTION ENVIRONMENT (Raspberry Pi):
-------------------------------------
1. Install libk8055:
   sudo apt-get install libk8055-dev

2. Use dome_config_production.json:
   {
     "hardware": {"mock_mode": false, "device_port": 0},
     "testing": {"smoke_test": false, "smoke_test_timeout": 30.0},
     "calibration": {
       "home_position": 225.0,      // YOUR calibrated value
       "ticks_to_degrees": 4.0      // YOUR calibrated value
     }
   }

3. Connect K8055 via USB

4. Test connection:
   python3 -c "
   from dome import EnhancedDome
   dome = EnhancedDome('dome_config_production.json')
   dome.print_status()
   "

CONTINUOUS INTEGRATION (CI/CD):
------------------------------
1. Use auto-detection or explicit mock mode
2. Set environment variable:
   export DOME_FORCE_MOCK=true

3. Use in dome.py:
   mock_mode = os.environ.get('DOME_FORCE_MOCK', 'false').lower() == 'true'

TROUBLESHOOTING:
---------------
• If hardware connection fails, dome automatically falls back to mock mode
• Check USB connection and permissions for K8055
• Verify libk8055 installation: lsusb should show Velleman device
• Check dome logs for hardware detection results
"""

    print(guide)


if __name__ == "__main__":
    print("🔭 ENHANCED DOME WITH HARDWARE DETECTION")
    print("=" * 60)

    demonstrate_configuration_scenarios()
    create_deployment_guide()
