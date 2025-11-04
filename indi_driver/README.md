# INDI K8055 Dome Driver

**Self-contained INDI dome driver for Velleman K8055-based observatory dome controllers.**

## Structure

```
indi_driver/
├── scripts/              # INDI implementation (the 11 scripts)
│   ├── connect.py        # Test hardware connection
│   ├── disconnect.py     # Safe shutdown
│   ├── status.py         # Report dome status
│   ├── open.py           # Open shutter
│   ├── close.py          # Close shutter
│   ├── park.py           # Move to home + close
│   ├── unpark.py         # Prepare for operations
│   ├── goto.py           # Move to azimuth
│   ├── move_cw.py        # Start CW rotation
│   ├── move_ccw.py       # Start CCW rotation
│   └── abort.py          # Emergency stop
├── lib/                  # Library components
│   ├── dome.py           # Core dome control class
│   ├── config.py         # Configuration loader
│   └── pyk8055_wrapper.py # K8055 hardware interface
├── dome_config.json.example # Configuration template
└── requirements.txt      # Dependencies (none for mock mode)
```

## Quick Setup

### Step 1: Install Hardware Dependencies (Raspberry Pi)
```bash
sudo apt-get update
sudo apt-get install libk8055-dev python3
```

### Step 2: Configure INDI dome_script driver
Point INDI dome_script driver to the scripts directory:
```
Script Folder: /path/to/indi_driver/scripts
Connect script: connect.py
Disconnect script: disconnect.py
Get status script: status.py
Open shutter script: open.py
Close shutter script: close.py
Park script: park.py
Unpark script: unpark.py
Goto script: goto.py
Move clockwise script: move_cw.py
Move counter clockwise script: move_ccw.py
Abort motion script: abort.py
```

### Step 3: Configure for your dome hardware
```bash
cp dome_config.json.example dome_config.json
# Edit dome_config.json with your specific dome calibration values
```

### Step 4: Test the installation
```bash
# Test from the indi_driver directory (where dome_config.json is located)
python scripts/connect.py && echo "SUCCESS"
python scripts/status.py
```

## Environment Variables

| Variable | Purpose | Values | Default |
|----------|---------|--------|---------|
| `DOME_TEST_MODE` | Override mode for testing | `smoke` = mock mode | none (hardware mode) |

**Note**: No environment variables are required for normal operation. The `DOME_TEST_MODE=smoke` variable is only used for development testing.

## Configuration

The `dome_config.json` file contains all user-configurable settings. Copy from `dome_config.json.example` and customize:

### Pin Assignments
Configure K8055 pin connections for your hardware:
- `encoder_a`, `encoder_b`: Position encoder inputs
- `home_switch`: Home position sensor input
- `shutter_upper_limit`, `shutter_lower_limit`: Shutter limit switches
- `dome_rotate`, `dome_direction`: Dome motor control outputs
- `shutter_move`, `shutter_direction`: Shutter motor control outputs

### Calibration (REQUIRED)
**You must calibrate these values for your specific dome:**
- `home_position`: Azimuth angle (degrees) where home switch triggers
- `ticks_to_degrees`: Encoder ticks per degree of dome rotation
- `poll_interval`: Hardware polling rate (seconds)

### Hardware Settings
- `mock_mode`: Set to `true` for testing without hardware, `false` for production
- `device_port`: K8055 device number (usually 0)

### Safety Timeouts
Critical safety limits to prevent damage:
- `emergency_stop_timeout`: Maximum time for emergency stop (2.0s recommended)
- `operation_timeout`: Maximum time for normal operations (60.0s recommended)
- `max_rotation_time`: Maximum time for full dome rotation (120.0s recommended)
- `max_shutter_time`: Maximum time for shutter operation (30.0s recommended)

### Testing Settings
Only used when `DOME_TEST_MODE=smoke` environment variable is set:
- `smoke_test`: Automatically set to `true` in test mode
- `smoke_test_timeout`: Reduced timeout for fast testing

## Architecture

```
INDI dome_script → scripts/ → lib/dome.py → lib/pyk8055_wrapper.py → K8055 Hardware
```

## Operating Modes

- **Hardware Mode** (default): Real K8055 operations (requires libk8055 on Raspberry Pi)
- **Mock Mode**: Safe operation without hardware (enabled via DOME_TEST_MODE=smoke environment variable)

This is a complete, self-contained INDI dome driver. Copy this entire directory to deploy.

## Troubleshooting

### Connection Issues
```bash
# Test hardware connection (run from indi_driver directory)
python scripts/connect.py && echo "SUCCESS" || echo "FAILED"

# Check if K8055 is detected
lsusb | grep -i velleman
```

### Configuration Issues
```bash
# Test with verbose output (run from indi_driver directory)
python scripts/status.py --verbose

# Verify configuration loads correctly
python -c "import sys; sys.path.insert(0, 'lib'); from config import load_config; print(load_config())"
```

### Common Problems
- **"Command exited with code 1"**: Hardware not connected or libk8055 not installed
- **Config not found warning**: Copy `dome_config.json.example` to `dome_config.json`
- **Calibration issues**: Verify `home_position` and `ticks_to_degrees` values for your dome

### Enable Test Mode
For safe testing without hardware:
```bash
export DOME_TEST_MODE=smoke
python scripts/connect.py && echo "SUCCESS"
```
