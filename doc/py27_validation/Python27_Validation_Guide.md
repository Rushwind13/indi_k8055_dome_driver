# Python 2.7 Validation Guide

Comprehensive guide for validating the INDI K8055 dome driver on Python 2.7 environments.

## Overview

This project provides a Python 2.7 compatible interface for the INDI K8055 dome driver, including comprehensive state persistence functionality. This guide covers validation, testing, and deployment for Python 2.7-only environments.

## Quick Start

### Prerequisites

- Python 2.7 installed on the system
- Virtual environment support
- Git repository cloned

### Setup Python 2.7 Environment

```bash
# Create Python 2.7 environment
make setup-py27

# Activate environment
source venv_py27/bin/activate

# Install dependencies (if needed)
cd indi_driver/python2
pip install -r requirements.txt  # if exists
```

### Run Validation

```bash
# Quick validation
make test-py27

# Complete validation with linting
make test-py27-full

# Verbose validation
make test-py27-verbose

# Persistence tests only
make test-py27-persistence
```

## Architecture

### Python 2.7 Driver Structure

```
indi_driver/python2/
├── lib/
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── dome.py             # Main dome control class
│   ├── persistence.py      # State persistence system
│   └── pyk8055_wrapper.py  # K8055 hardware interface
├── scripts/
│   ├── status.py           # Status reporting (with persistence)
│   ├── goto.py             # Position control (with persistence)
│   ├── park.py             # Home positioning (with persistence)
│   ├── move_cw.py          # Clockwise movement (with persistence)
│   ├── move_ccw.py         # Counter-clockwise movement (with persistence)
│   ├── open.py             # Shutter open (with persistence)
│   └── close.py            # Shutter close (with persistence)
└── dome_config.json        # Configuration file
```

### Key Features

1. **State Persistence**: All dome states persist between script executions
2. **Python 2.7 Compatibility**: No f-strings, modern syntax, or Python 3 features
3. **Mock Mode**: Safe testing without hardware requirements
4. **Script Integration**: Existing INDI scripts enhanced with persistence

## Validation Tests

### Core Validation (`validate_py27.py`)

Comprehensive validation covering:

- **Module Imports**: All required modules load without errors
- **Dome Creation**: Dome objects can be created with mock configuration
- **Basic Operations**: Position reading, state management work correctly
- **Persistence**: State save/restore functionality operates properly
- **Script Integration**: INDI scripts have persistence calls
- **Python 2.7 Compatibility**: Code uses Python 2.7 compatible syntax

### Persistence Tests (`test_persistence_py27.py`)

Detailed persistence testing including:

- Complete sensor state persistence (position, encoders, home, shutter, movement)
- Error handling for missing/corrupted state files
- Multiple script execution simulation
- Convenience function validation
- Integration with existing dome objects

### Test Execution

```bash
# Individual test files
python test/python2/validate_py27.py                    # Core validation
python test/python2/validate_py27.py --verbose          # Verbose output
python test/python2/validate_py27.py --persistence-only # Persistence only
python test/python2/test_persistence_py27.py            # Detailed persistence tests

# Test runner
python test/python2/validate_py27.py                   # All tests
python test/python2/validate_py27.py --verbose         # Verbose mode
python test/python2/validate_py27.py --persistence-only # Persistence only
```

## State Persistence System

### Architecture

The persistence system saves complete dome state between script executions:

```json
{
  "timestamp": "2025-11-04T08:00:00.000000",
  "script": "goto",
  "position": 45.0,
  "encoder_a": 180,
  "encoder_b": 45,
  "is_home": false,
  "is_turning": false,
  "direction": false,
  "shutter_open": false,
  "shutter_closed": true,
  "shutter_opening": false,
  "shutter_closing": false,
  "pins": { ... },
  "calibration": { ... }
}
```

### Integration Pattern

Each INDI script follows this pattern:

```python
#!/usr/bin/env python
import os
import sys

def main():
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
    from dome import Dome
    from persistence import restore_state, save_state

    try:
        dome = Dome()
        restore_state(dome)  # Restore previous state

        # ... dome operations ...

        save_state(dome, "script_name")  # Save current state
        sys.exit(0)
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Usage Examples

```python
# Direct persistence usage
from persistence import DomePersistence

persistence = DomePersistence()
dome = Dome(config)

# Save complete state
persistence.save_dome_state(dome, "my_script")

# Load and restore state
state = persistence.load_dome_state()
persistence.restore_dome_state(dome, state)

# Convenience functions
from persistence import save_state, restore_state, show_state

save_state(dome, "script_name")
restore_state(dome)
show_state()  # Display current persisted state
```

## Deployment

### Target Environment Requirements

- Python 2.7.x
- Velleman K8055 USB interface board (or mock mode for testing)
- File system write access for state persistence
- INDI telescope software (for integration)

### Deployment Steps

1. **Validate locally**:
   ```bash
   make test-py27-full
   ```

2. **Copy Python 2.7 files** to target system:
   ```bash
   scp -r indi_driver/python2/ user@target:/path/to/indi/
   ```

3. **Test on target system**:
   ```bash
   # On target system
   cd /path/to/indi/python2
   python scripts/status.py
   ```

4. **Configure INDI** to use Python 2.7 scripts

### Production Configuration

Update `dome_config.json` for production:

```json
{
    "pins": {
        "encoder_a": 1,
        "encoder_b": 5,
        "home_switch": 2,
        ...
    },
    "calibration": {
        "home_position": 225,
        "ticks_to_degrees": 4.0,
        "poll_interval": 0.5
    },
    "hardware": {
        "mock_mode": false,
        "device_port": 0
    },
    "safety": {
        "emergency_stop_timeout": 2.0,
        "operation_timeout": 60.0,
        "max_rotation_time": 120.0,
        "max_shutter_time": 30.0
    }
}
```

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure Python 2.7 environment is active
source venv_py27/bin/activate
which python  # Should show venv_py27/bin/python
```

**Hardware Connection Issues**
```bash
# Test in mock mode first
python -c "
import sys, os
sys.path.insert(0, 'indi_driver/python2/lib')
from dome import Dome
config = {'hardware': {'mock_mode': True, 'device_port': 0}, 'testing': {'smoke_test': True, 'smoke_test_timeout': 3.0}}
dome = Dome(config)
print('Mock mode working')
"
```

**Persistence Issues**
```bash
# Check state file location and permissions
python -c "
import sys, os
sys.path.insert(0, 'indi_driver/python2/lib')
from persistence import show_state
show_state()
"
```

**Script Integration Issues**
```bash
# Verify script has persistence imports
grep -n "from persistence import" indi_driver/python2/scripts/*.py
```

### Debugging Commands

```bash
# Test individual components
python test/python2/validate_py27.py --verbose
python test/python2/test_persistence_py27.py --demo

# Check module availability
python -c "import pyk8055_wrapper; print('K8055 wrapper OK')"
python -c "import dome; print('Dome module OK')"
python -c "import persistence; print('Persistence module OK')"

# Test persistence directly
python indi_driver/python2/lib/persistence.py --test
python indi_driver/python2/lib/persistence.py --show
```

## Make Targets

| Target | Description |
|--------|-------------|
| `make setup-py27` | Create Python 2.7 virtual environment |
| `make test-py27` | Run core Python 2.7 validation |
| `make test-py27-verbose` | Run validation with verbose output |
| `make test-py27-persistence` | Run persistence tests only |
| `make test-py27-full` | Run complete validation with linting |
| `make py27-validation` | Complete validation workflow |

## Expected Results

### Successful Validation Output

```
Python 2.7 Dome Driver Validation Suite
=============================================
Python version: 2.7.18

1. Testing module imports...
  ✓ All module imports successful
2. Testing dome object creation...
  ✓ Dome creation and basic operations successful
3. Testing persistence functionality...
  ✓ Persistence functionality working correctly
4. Testing INDI script integration...
  ✓ All scripts have persistence integration
5. Testing Python 2.7 compatibility...
  ✓ Python 2.7 compatibility verified

=============================================
VALIDATION SUMMARY
Passed: 5
Failed: 0
Total:  5

🎉 ALL VALIDATION TESTS PASSED!
Python 2.7 dome driver is ready for deployment.
```

### Success Criteria

✅ **Ready for Deployment** when:

1. All validation tests pass
2. Persistence tests pass (8/8 tests)
3. No linting errors in Python 2.7 code
4. Mock mode operations work correctly
5. Script integration verified

## Development Workflow

1. **Make changes** to Python 2.7 code in `indi_driver/python2/`
2. **Test locally**: `make test-py27-full`
3. **Fix any issues** reported by validation
4. **Deploy to target**: Copy files and test on Python 2.7 system
5. **Verify operation**: Test with actual hardware (carefully)

## Support

This Python 2.7 validation system ensures the dome driver works reliably on legacy Python 2.7 systems while maintaining full functionality and state persistence.
