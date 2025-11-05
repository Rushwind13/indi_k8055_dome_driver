# Relay Control Logic Analysis

**INDI K8055 Dome Driver - A3: Relay Control Logic Analysis Results**

## 📋 Executive Summary

**Status**: ⚠️ **Logic Issues Found**  
**Critical Issues**: 3 relay control problems identified  
**Safety Issues**: 1 emergency stop sequence issue  
**Timing Issues**: 2 relay sequencing problems  

## 🔍 Current Relay Control Patterns

### 🔄 Rotation Motor Control Analysis

#### Direction Control Logic
**Method**: `set_rotation(self, dir)`
```python
def set_rotation(self, dir):
    self.dir = dir
    if dir == self.CCW:
        self.dome.digital_on(self.DOME_DIR)    # CCW = True = ON
    else:
        self.dome.digital_off(self.DOME_DIR)   # CW = False = OFF
```

**Analysis**:
- ✅ **Direction Logic Correct**: CW=OFF, CCW=ON matches hardware expectations
- ✅ **State Tracking**: `self.dir` properly updated
- ⚠️ **Timing Issue**: No delay between direction set and motor enable
- ⚠️ **Missing Validation**: No verification that direction relay activated

#### Enable Control Logic  
**Locations**: `home()`, `rotation()` methods
```python
# Pattern in home() method:
self.dome.digital_on(self.DOME_ROTATE)   # Enable motor
# ... movement logic ...
self.dome.digital_off(self.DOME_ROTATE)  # Disable motor

# Pattern in rotation() method:
if not self.is_turning:
    self.dome.digital_on(self.DOME_ROTATE)  # Enable motor
    self.is_turning = True
# ... movement logic ...  
self.dome.digital_off(self.DOME_ROTATE)     # Disable motor
```

**Analysis**:
- ✅ **Enable/Disable Pattern**: Proper ON/OFF control
- ✅ **State Tracking**: `self.is_turning` flag maintained
- ❌ **Critical Timing Issue**: Enable happens BEFORE direction is verified
- ❌ **No Direction Validation**: Motor could run in wrong direction

### 🏠 Homing Operation Analysis

**Method**: `home()`
**Relay Sequence**:
1. Direction set via `set_rotation()` call (in `cw()` or `ccw()`)
2. Enable motor: `digital_on(DOME_ROTATE)`
3. Poll home switch while rotating
4. Disable motor: `digital_off(DOME_ROTATE)` when home found

**Issues Found**:
- ⚠️ **No Relay Settling Time**: Direction and enable happen immediately
- ⚠️ **Missing Watchdog**: TODO comment indicates incomplete safety
- ✅ **Home Switch Logic**: Properly stops when switch activates

### 🎯 Rotation by Amount Analysis

**Method**: `rotation(amount=0)`
**Known Issues**:
```python
while (self.dome.counter_read(self.A) < target_pos):  # Bug: only works for one direction
```

**Problems Identified**:
- ❌ **Bidirectional Bug**: Only works for positive rotation (CW direction)
- ❌ **No CCW Support**: Counter logic assumes forward counting only
- ❌ **Direction Ignored**: Doesn't consider `self.dir` for movement direction
- ❌ **Position Tracking Error**: Uses only encoder A, ignores direction

## 🚪 Shutter Motor Control Analysis

### Opening Operation
**Method**: `shutter_open()`
**Relay Sequence**:
```python
self.dome.digital_on(self.SHUTTER_MOVE)      # Enable shutter motor
self.dome.digital_off(self.SHUTTER_DIR)     # Direction: OFF = Opening
```

### Closing Operation  
**Method**: `shutter_close()`
**Relay Sequence**:
```python
self.dome.digital_on(self.SHUTTER_MOVE)      # Enable shutter motor  
self.dome.digital_on(self.SHUTTER_DIR)      # Direction: ON = Closing
```

**Analysis**:
- ✅ **Direction Logic Correct**: OFF=Open, ON=Close
- ✅ **State Tracking**: `is_opening`/`is_closing` flags maintained
- ✅ **Safety Checks**: Home position validation and operation conflict checks
- ⚠️ **Timing Issue**: Enable and direction set simultaneously
- ⚠️ **No Status Verification**: No confirmation shutter actually moved

## 🚨 Emergency Stop Analysis

### Rotation Emergency Stop
**Method**: `rotation_stop()`
```python
self.dome.digital_off(self.DOME_ROTATE)  # Disable rotation
self.dome.digital_off(self.DOME_DIR)     # Clear direction  
```

### Shutter Emergency Stop
**Method**: `shutter_stop()`
```python
self.dome.digital_off(self.SHUTTER_MOVE)  # Disable shutter
self.dome.digital_off(self.SHUTTER_DIR)   # Clear direction
```

**Analysis**:
- ✅ **Immediate Disable**: Motor enable relays turned off first
- ✅ **Direction Clear**: Direction relays also cleared
- ⚠️ **No Sequence Delay**: Both relays turned off simultaneously
- ⚠️ **Missing Verification**: No confirmation relays actually turned off

## 🔧 Relay Timing and Sequencing Issues

### Issue 1: No Relay Settling Time
**Problem**: Direction and enable relays controlled simultaneously
**Risk**: Motor could start before direction relay has settled
**Standard Practice**: 10-50ms delay between direction set and motor enable

**Locations**:
- `shutter_open()`: Lines 242-243
- `shutter_close()`: Lines 263-264  
- `home()` and `rotation()`: Via `set_rotation()` + immediate enable

### Issue 2: Missing Direction Validation
**Problem**: No verification that direction relay actually activated
**Available Solution**: Read DI4 (direction telemetry) to confirm DO2 state
**Impact**: Motor could run in wrong direction due to relay failure

### Issue 3: Bidirectional Rotation Bug
**Problem**: `rotation()` method only supports forward counting
**Root Cause**: Uses simple `< target_pos` comparison
**Fix Required**: Direction-aware position comparison logic

## 📊 Relay State Mapping

### Current Relay States

| Function | Enable Pin | Enable State | Direction Pin | Direction State | Notes |
|----------|------------|--------------|---------------|-----------------|-------|
| **CW Rotation** | DO1 (dome_rotate) | ON | DO2 (dome_direction) | OFF | ✅ Correct |
| **CCW Rotation** | DO1 (dome_rotate) | ON | DO2 (dome_direction) | ON | ✅ Correct |
| **Shutter Open** | DO5 (shutter_move) | ON | DO6 (shutter_direction) | OFF | ✅ Correct |
| **Shutter Close** | DO5 (shutter_move) | ON | DO6 (shutter_direction) | ON | ✅ Correct |
| **Emergency Stop** | All Enable Pins | OFF | All Direction Pins | OFF | ✅ Correct |

### Hardware Constants Validation
```python
self.CW = False   # ✅ Correct: CW = direction relay OFF  
self.CCW = True   # ✅ Correct: CCW = direction relay ON
```

## 🎯 Critical Issues Requiring Immediate Fix

### Priority 1: Relay Sequencing (Safety Critical)
**File**: `dome.py` - All motor control methods
**Issue**: Direction and enable relays activated simultaneously
**Risk**: Motor direction undefined during startup transient
**Solution**: Add 20ms delay between direction set and motor enable

### Priority 2: Bidirectional Rotation Bug  
**File**: `dome.py` - `rotation()` method, line ~150
**Issue**: Only works for positive encoder counts (one direction)
**Impact**: Rotation commands fail in CCW direction
**Solution**: Implement direction-aware position tracking

### Priority 3: Direction Telemetry Implementation
**File**: `dome.py` - Add new method  
**Issue**: DO2→DI4 telemetry wiring not used
**Benefit**: Validate direction relay activation before motor enable
**Solution**: Add `verify_direction()` method reading DI4

## 🔧 Recommended Relay Control Sequence

### Safe Motor Start Sequence
1. **Stop Motion**: Ensure enable relay is OFF
2. **Set Direction**: Activate direction relay (DO2 or DO6)  
3. **Settling Delay**: Wait 20-50ms for relay to settle
4. **Verify Direction**: Read telemetry (DI4) to confirm direction
5. **Enable Motor**: Activate enable relay (DO1 or DO5)
6. **Monitor Motion**: Track position and status during movement

### Safe Motor Stop Sequence  
1. **Disable Motor**: Turn OFF enable relay immediately
2. **Settling Delay**: Wait 10ms for motor to stop
3. **Clear Direction**: Turn OFF direction relay
4. **Update State**: Clear motion flags and update position

## 📋 Testing Requirements

### Relay Timing Tests Needed
- [ ] Measure actual relay activation time  
- [ ] Test direction stability during enable transient
- [ ] Verify emergency stop response time (<2 seconds)
- [ ] Test relay state persistence after power cycle

### Direction Validation Tests Needed  
- [ ] Test DO2→DI4 telemetry feedback loop
- [ ] Verify direction commands match actual relay states
- [ ] Test direction change timing and reliability

### Bidirectional Rotation Tests Needed
- [ ] Test CW rotation accuracy over various distances
- [ ] Test CCW rotation accuracy over various distances  
- [ ] Verify encoder counting in both directions
- [ ] Test rotation reversals and direction changes

---

**Analysis Date**: November 4, 2025  
**Status**: Relay control logic analysis complete, critical issues identified  
**Next Action**: Implement relay sequencing fixes and bidirectional rotation logic