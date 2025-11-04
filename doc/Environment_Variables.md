# Environment Variables Reference

**INDI K8055 Dome Driver - Complete Environment Variables Guide**

This document lists all environment variables used by the dome driver system for configuration, testing, and safety.

---

## 🎯 Core Testing Variables

### DOME_TEST_MODE
**Purpose**: Controls test execution mode and hardware interaction
**Values**: `smoke` (default), `hardware`
**Used By**: All test frameworks, Makefile targets

```bash
# Run tests in mock mode (safe, no hardware required)
export DOME_TEST_MODE=smoke

# Run tests with real hardware
export DOME_TEST_MODE=hardware
```

**Impact:**
- `smoke`: Uses mock K8055 interface, fast execution, safe for development
- `hardware`: Connects to real K8055 hardware, slower execution, requires physical setup

**Default**: `smoke` if not set

---

## 🌧️ Weather Safety Variables

### WEATHER_RAINING
**Purpose**: Rain detection for shutter safety control
**Values**: `true`, `false` (default: `true` for safety)
**Used By**: Test framework, safety systems

```bash
# Indicate clear weather (enables shutter operations)
export WEATHER_RAINING=false

# Indicate rain conditions (blocks shutter operations)
export WEATHER_RAINING=true
```

**Safety Behavior:**
- `true`: Shutter operations blocked unless override is set
- `false`: All operations allowed normally
- Rotation operations continue regardless of rain status

### SHUTTER_RAIN_OVERRIDE
**Purpose**: Force shutter operations despite rain detection
**Values**: `true`, `false` (default), any non-empty string
**Used By**: Safety validation systems

```bash
# Force shutter operations in rain (use with caution)
export SHUTTER_RAIN_OVERRIDE=true

# Respect rain safety (default)
export SHUTTER_RAIN_OVERRIDE=false
```

**Safety Warning**: Only use override when absolutely necessary and with proper precautions.

---

## 🐍 Python Environment Variables

### PYTHONPATH
**Purpose**: Module path for pyk8055 hardware library access
**Values**: Colon-separated directory paths
**Used By**: All test runners, driver scripts

```bash
# System-wide pyk8055 installation (recommended)
export PYTHONPATH="/usr/local/lib/python3.x/site-packages:$PYTHONPATH"

# Custom build location
export PYTHONPATH="/tmp/libk8055/src/pyk8055:$PYTHONPATH"

# Multiple paths
export PYTHONPATH="/path/to/pyk8055:/other/path:$PYTHONPATH"
```

**Common Locations:**
- **System Install**: `/usr/local/lib/python3.x/site-packages`
- **Local Build**: `/tmp/libk8055/src/pyk8055`
- **User Install**: `~/.local/lib/python3.x/site-packages`

**Troubleshooting**: If you see `ModuleNotFoundError: No module named 'pyk8055'`, check this variable.

---

## 🔧 Development and Testing Variables

### DOME_FORCE_MOCK
**Purpose**: Force mock mode in demo and example scripts
**Values**: `true`, `false` (default)
**Used By**: `doc/enhanced_dome_example.py`, demonstration scripts

```bash
# Force demonstration scripts to use mock mode
export DOME_FORCE_MOCK=true

# Allow demonstration scripts to detect hardware
export DOME_FORCE_MOCK=false
```

---

## 📋 Variable Usage by Component

### Test Framework (`test/run_tests.py`, `test/integration/test_base.py`)
- **DOME_TEST_MODE**: Test execution mode selection
- **WEATHER_RAINING**: Weather simulation for safety testing
- **SHUTTER_RAIN_OVERRIDE**: Safety override testing
- **PYTHONPATH**: Module path for test imports

### Makefile Targets
- **DOME_TEST_MODE**: Automatically set for hardware test targets
- **WEATHER_RAINING**: Displayed in hardware test status

### Documentation Examples
- **DOME_TEST_MODE**: Used in all hardware testing examples
- **WEATHER_RAINING**: Demonstrated in safety scenarios
- **PYTHONPATH**: Installation and troubleshooting guides

### Driver Scripts
- **PYTHONPATH**: Implicit dependency for pyk8055 module import

---

## 🎯 Quick Reference by Use Case

### Initial Development
```bash
# Safe development with mock hardware
export DOME_TEST_MODE=smoke
# PYTHONPATH not required for mock mode
```

### Hardware Installation
```bash
# Set Python path for pyk8055 module
export PYTHONPATH="/tmp/libk8055/src/pyk8055:$PYTHONPATH"

# Test hardware connectivity
export DOME_TEST_MODE=hardware
export WEATHER_RAINING=false
```

### Production Hardware Testing
```bash
# Full hardware test suite
export DOME_TEST_MODE=hardware
export WEATHER_RAINING=false
export PYTHONPATH="/usr/local/lib/python3.x/site-packages:$PYTHONPATH"
```

### Rainy Weather Testing
```bash
# Test rain safety systems
export DOME_TEST_MODE=hardware
export WEATHER_RAINING=true
# Shutter operations will be blocked unless override is set
```

### Emergency Shutter Operations
```bash
# Force shutter operations despite rain (use carefully)
export WEATHER_RAINING=true
export SHUTTER_RAIN_OVERRIDE=true
export DOME_TEST_MODE=hardware
```

---

## 🛡️ Safety Considerations

### Default Safe Values
The system defaults to safe values when variables are not set:
- **DOME_TEST_MODE**: Defaults to `smoke` (mock mode)
- **WEATHER_RAINING**: Defaults to `true` (rain detected)
- **SHUTTER_RAIN_OVERRIDE**: Defaults to `false` (no override)

### Production Recommendations
For production deployment:
1. **Set PYTHONPATH** in system startup scripts (`/etc/environment` or `~/.bashrc`)
2. **Integrate weather station** to automatically set `WEATHER_RAINING`
3. **Avoid persistent overrides** - use `SHUTTER_RAIN_OVERRIDE` only when needed
4. **Monitor test mode** - ensure production uses `hardware` mode appropriately

### Security Notes
- Environment variables are visible to all processes run by the same user
- No sensitive information should be stored in these variables
- Use appropriate file permissions for scripts that set these variables

---

## 🔍 Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'pyk8055'"**
- Check PYTHONPATH includes pyk8055 module location
- Verify pyk8055 is properly installed
- Try absolute paths in PYTHONPATH

**"Hardware tests not running"**
- Ensure DOME_TEST_MODE=hardware is set
- Check that hardware test targets in Makefile use correct mode

**"Shutter operations blocked"**
- Check WEATHER_RAINING setting
- Use SHUTTER_RAIN_OVERRIDE=true if operations must proceed
- Verify weather detection integration

**"Tests use wrong mode"**
- Environment variables must be exported, not just set
- Check that test runners inherit correct environment
- Verify Makefile targets set variables properly

### Diagnostic Commands

```bash
# Check current environment variable values
env | grep -E "DOME_|WEATHER_|SHUTTER_|PYTHONPATH"

# Test Python module import
python3 -c "import sys; print('\\n'.join(sys.path))"
python3 -c "import pyk8055; print('✅ pyk8055 available')"

# Verify test mode detection
cd /path/to/indi_k8055_dome_driver
python3 -c "
import os
mode = os.environ.get('DOME_TEST_MODE', 'smoke')
rain = os.environ.get('WEATHER_RAINING', 'true')
override = os.environ.get('SHUTTER_RAIN_OVERRIDE', 'false')
print(f'Test Mode: {mode}')
print(f'Weather Raining: {rain}')
print(f'Shutter Override: {override}')
"
```

---

*This reference covers all environment variables used by the INDI K8055 Dome Driver system. For setup help, see the Installation Guide. For operational guidance, see the User Guide.*
