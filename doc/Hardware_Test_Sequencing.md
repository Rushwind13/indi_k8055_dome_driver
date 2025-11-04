# Hardware Test Sequencing Guide

**INDI K8055 Dome Driver - Production Hardware Testing**

This document describes the hardware test sequencing system implemented for Task 7 of the Production Readiness Tasks. The system ensures safe, ordered testing of real dome hardware with proper dependency management and isolation.

## 🎯 Quick Start

### Minimal Hardware Validation (Recommended First Step)
```bash
# Set hardware mode and run safe initial tests
export DOME_TEST_MODE=hardware
make test-hardware-safe
```
**Duration**: <2 minutes
**Movements**: Short rotations only (<5 seconds)
**Safety**: Weather-aware, abort system validation

### Complete Hardware Integration
```bash
# Full hardware test sequence with proper ordering
export DOME_TEST_MODE=hardware
make test-hardware-sequence
```
**Duration**: 10-20 minutes
**Movements**: Full dome operations including homing, goto, calibration
**Safety**: Complete dependency-ordered sequence

## 🚀 Test Sequence Phases

### Phase 1: Hardware Startup Sequence
```bash
make test-hardware-startup
```

**Physical Actions Expected:**
1. **Connection Test** (5 seconds)
   - when user performs this step, the dome should connect and respond within 5 seconds
2. **Short Movement Test** (2 seconds)
   - when user performs this step, the dome should rotate for 2 seconds in the CW direction
3. **Safety Validation** (2 seconds)
   - when user performs this step, the abort should stop any motion within 2 seconds

**Safety Features:**
- Weather rain detection (blocks shutter, allows rotation)
- Automatic timeout warnings for connection issues
- Emergency abort validation before any movement tests

### Phase 2: Dependency-Ordered Integration Tests
- Basic connectivity tests (no dependencies)
- Homing operations (requires connection)
- Position-dependent tests (requires homing)
- Calibration tests (requires stable operations)

### Phase 3: Calibration Data Capture
```bash
make test-calibrate
```
- Position accuracy measurement (8 test positions)
- Home repeatability analysis (5 trials with statistics)
- Rotation timing calibration (multiple directions/distances)

## 🛡️ Safety Features

### Weather Safety
```bash
# Rain detected - restricts shutter operations
export WEATHER_RAINING=true
make test-hardware-safe

# Override for shutter testing (use with caution)
export SHUTTER_RAIN_OVERRIDE=true
```

### Test Dependencies
Tests automatically check dependencies and will:
- Home the dome before position-dependent tests
- Validate connectivity before movement tests
- Ensure safe state between isolation-required tests

### Emergency Controls
- Every test has automatic abort script execution in teardown
- Timeout handling with user warnings
- Hardware session state tracking prevents unsafe operations

## 🔧 Test Infrastructure

### Hardware State Management
The system tracks:
- Dome homed status
- Current azimuth position
- Last operation performed
- Weather conditions
- Test sequence completion

### Test Decorators
```python
@requires_hardware_state(state="homed", dependencies=["test_park_script"])
def test_goto_script(self):
    # Test will automatically ensure dome is homed and park script has completed
    pass

@hardware_startup_sequence(short_movement=True, check_weather=True)
def test_hardware_connectivity(self):
    # Test includes automatic short movement validation and weather checks
    pass
```

## 📋 Available Make Targets

| Target | Duration | Purpose | Safety Level |
|--------|----------|---------|--------------|
| `test-hardware-safe` | <2 min | Initial validation | Minimal movement |
| `test-hardware-startup` | <5 min | Startup sequence | Short movements |
| `test-hardware-sequence` | 10-20 min | Full integration | Complete testing |
| `test-calibrate` | 5-15 min | Calibration data | Precision movements |

## 🌧️ Weather Considerations

**Current Weather**: It is currently raining (as noted in user requirements)

**Behavior:**
- Rotation tests: ✅ Proceed normally (safe in rain)
- Shutter tests: ⚠️ Blocked unless `SHUTTER_RAIN_OVERRIDE=true`
- Movement tests: ✅ Proceed with rain status logging

**Rain Override Example:**
```bash
export WEATHER_RAINING=true
export SHUTTER_RAIN_OVERRIDE=true  # Only if confirmed safe
export DOME_TEST_MODE=hardware
make test-hardware-sequence
```

## 🎯 Expected Physical Outputs

### During Hardware Startup:
1. **LED indicators** should show K8055 board activity
2. **Dome rotation** should be clearly visible for 2 seconds
3. **Rotation should stop immediately** when abort is called
4. **No shutter movement** unless rain override is set

### During Full Sequence:
1. **Homing operation** - dome rotates to find home position
2. **Position tests** - dome moves to 8 different azimuth positions
3. **Repeatability tests** - multiple home operations for statistics
4. **Calibration movements** - timed rotations for speed measurement

## 🚫 Error Handling

### Timeout Warnings
If operations approach timeout limits, users see:
```
⚠️  WARNING: Connection approaching timeout - check hardware connection
```

### Dependency Failures
If test dependencies aren't met:
```
⚠️  Test test_goto_script has unmet dependencies: ['test_park_script']
```

### Weather Restrictions
When rain blocks shutter operations:
```
🌧️  Blocking shutter operations - rain detected and no override
    Set SHUTTER_RAIN_OVERRIDE=true to force shutter operations
```

## 🎉 Success Indicators

### Hardware Startup Success:
```
✅ Hardware startup sequence completed successfully!
   System ready for extended hardware integration testing
```

### Full Sequence Success:
```
✅ Full hardware test sequence complete!
🎉 System validated for production hardware integration!
```

## 🔗 Integration with Existing Infrastructure

The hardware test sequencing system:
- ✅ **Maximizes reuse** of existing test infrastructure
- ✅ **Leverages existing** safety teardown patterns
- ✅ **Uses existing** timeout and configuration systems
- ✅ **Builds on existing** calibration test suite
- ✅ **Integrates with existing** Makefile targets

No new files were created unnecessarily - all functionality was added to existing:
- `test/integration/test_base.py` - Base infrastructure with sequencing
- `test/integration/test_indi_scripts.py` - Enhanced with decorators
- `test/run_tests.py` - Added hardware session management
- `Makefile` - Added sequencing targets

This approach ensures **minimal redundancy** and **maximum maintainability** as requested.
