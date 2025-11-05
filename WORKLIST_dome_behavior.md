# WORKLIST: Dome Control Behavior Validation and Refinement

**INDI K8055 Dome Driver - Dome Control Behavior Analysis and Enhancement**

This worklist contains all tasks required to validate dome control behavior, enhance the driver for proper relay/motor control, and demonstrate correct behavior with real physical hardware.

## 🎯 Project Overview

The dome uses **4 relays total** for motor control:
- **Rotation Motor**: Direction relay (CW/CCW) + Enable relay (ON/OFF)
- **Shutter Motor**: Direction relay (OPEN/CLOSE) + Enable relay (ON/OFF)

**Key Requirements:**
- **Production code requirements**: Python2.7 for all `indi_driver` code; use Python3 code and tests only for reference
- **Non-blocking operations**: Set relays quickly, let polling/timing handle duration
- **No shutter telemetry**: Use fixed timing with automatic limit switch cutoff
- **Encoder-based rotation**: 2-bit Gray Code from encoder A/B pins
- **Fast polling**: Ensure home switch and encoder are read quickly enough

## 📋 Task Categories

### 🔌 A. Hardware Wiring Connection Analysis

#### A1. Create K8055 Wiring Connection Table
**Priority: HIGH** ⭐⭐⭐ **[COMPLETED]**
- [x] Document current pin assignments from `dome_config.json`
- [x] Create table showing each K8055 pin and its physical function
- [x] Map digital outputs to specific relays (direction vs enable)
- [x] Map digital inputs to specific sensors/switches
- [x] Map analog inputs to limit switch telemetry (N/A - no telemetry used)
- [x] Identify unused pins and their potential uses
- [x] Document relay wiring logic (normally open/closed states)
- [x] Document direction telemetry wiring (DO2 → DI4)
**Location:** `/doc/K8055_Wiring_Connection_Table.md`

#### A2. Validate Current Pin Configuration
**Priority: HIGH** ⭐⭐⭐ **[COMPLETED]**
- [x] Review current pin assignments in `dome_config.json`
- [x] Check for pin conflicts using existing `k8055_pin_tester.py`
- [x] Verify digital input/output ranges are correct (1-5 for inputs, 1-8 for outputs)
- [x] Test pin configuration with hardware (validation tool run)
- [x] Document any discovered conflicts or issues
**Issues Found:** 2 configuration errors (missing shutter telemetry, unused direction pin)
**Location:** `/doc/Pin_Configuration_Analysis.md`

#### A3. Analyze Relay Control Logic
**Priority: HIGH** ⭐⭐⭐ **[COMPLETED]**
- [x] Document current relay control patterns in `dome.py`
- [x] Map `dome_rotate`/`dome_direction` pins to motor control logic
- [x] Map `shutter_move`/`shutter_direction` pins to motor control logic
- [x] Verify CW/CCW direction mappings (`self.CW = False`, `self.CCW = True`)
- [x] Document the enable/disable sequence timing
- [x] Identify any logic errors in current implementation
**Issues Found:** 3 critical relay control problems (timing, bidirectional bug, no validation)
**Location:** `/doc/Relay_Control_Logic_Analysis.md`

### 🔄 B. Motor Control Behavior Enhancement

#### B1. Implement Non-Blocking Rotation Control
**Priority: HIGH** ⭐⭐⭐ **[COMPLETED]**
- [x] Modify `cw()` and `ccw()` methods for non-blocking operation
- [x] Separate "start rotation" from "wait for completion"
- [x] Add `start_rotation()` method that sets relays and returns immediately
- [x] Add `stop_rotation()` method that clears relays immediately
- [x] Update `rotation()` method to use non-blocking pattern
- [x] Ensure proper relay state management during operations
- [x] Implement proper relay sequencing with 20ms timing delays
- [x] Add safety checks to prevent conflicting operations
**Issues Fixed:** Relay timing safety, bidirectional rotation bug, configuration errors
**Location:** `/doc/B1_Non_Blocking_Rotation_Implementation.md`

#### B2. Fix Rotation Direction Logic
**Priority: HIGH** ⭐⭐⭐ **[COMPLETED via B1]**
- [x] Fix the "Bug: only works for one direction" comment in `rotation()` method
- [x] Implement proper bidirectional rotation based on target position
- [x] Add logic to determine shortest path to target (CW vs CCW)
- [x] Update encoder position tracking for both directions
- [x] Test rotation accuracy in both directions
**Note:** This was completed as part of B1 implementation
**Bidirectional rotation now works correctly for both CW and CCW directions**

#### B3. Enhance Shutter Control with Proper Timing
**Priority: MEDIUM** ⭐⭐
- [ ] Implement non-blocking shutter operations
- [ ] Add `start_shutter_open()` and `start_shutter_close()` methods
- [ ] Create timing-based shutter completion detection
- [ ] Add shutter state tracking during operations
- [ ] Implement proper timeout handling for shutter operations
- [ ] Document shutter limit switch behavior (automatic power cutoff)

#### B4. Implement Rotation Direction Telemetry
**Priority: MEDIUM** ⭐⭐
- [ ] Add code to read rotation direction from digital input (if connected)
- [ ] Verify current direction matches commanded direction
- [ ] Add direction telemetry to status reporting
- [ ] Implement direction feedback validation
- [ ] Document the telemetry pin configuration

### 🔍 C. Encoder and Sensor Polling Enhancement

#### C1. Implement 2-Bit Gray Code Encoder Reading
**Priority: HIGH** ⭐⭐⭐ **[COMPLETED]**
- [x] Create function to read encoder A and B simultaneously (via clean wrapper interface)
- [x] Implement Gray Code state change detection
- [x] Add direction detection based on encoder state transitions
- [x] Calculate rotation speed based on encoder timing
- [x] Add encoder error detection (missed transitions)
- [x] Test encoder polling frequency against maximum dome rotation speed
- [x] Integrate encoder tracking into rotation and homing operations
- [x] Expose ReadAllDigital via clean wrapper interface (dome abstraction)
**Implementation:** Complete 2-bit Gray Code system with CW/CCW detection
**Location:** `/doc/C1_Gray_Code_Encoder_Implementation.md`

#### C2. Optimize Home Switch Polling
**Priority: HIGH** ⭐⭐⭐ **[COMPLETED]**
- [x] Analyze current home switch polling in `home()` method
- [x] Calculate minimum polling frequency needed for reliable detection
- [x] Implement fast polling during homing operations (50ms vs 500ms)
- [x] Add home switch signal duration measurement/calibration
- [x] Ensure home switch detection works at maximum rotation speed
- [x] Add debugging output for home switch timing
- [x] Implement signal debouncing and validation (100ms threshold)
- [x] Add comprehensive diagnostic methods for performance monitoring
**Implementation:** Fast polling optimization with 10x speed improvement and noise rejection
**Location:** `/doc/C2_Home_Switch_Polling_Optimization.md`

#### C3. Add Encoder Calibration and Validation
**Priority: MEDIUM** ⭐⭐ **[COMPLETED]**
- [x] Create encoder calibration routine to measure actual encoder pulses per degree
- [x] Validate `ticks_to_degrees` configuration value against real hardware
- [x] Add encoder consistency checking (A vs B phase relationship)
- [x] Implement encoder error detection and recovery mechanisms
- [x] Add encoder fault diagnosis and automatic recovery procedures
- [x] Create comprehensive test suite for encoder calibration validation
- [x] Document encoder calibration procedure with troubleshooting guide
**Implementation:** Automated calibration with accuracy validation, error recovery, and comprehensive diagnostics
**Location:** `/doc/C3_Encoder_Calibration_Guide.md`

### 🧪 D. Testing and Validation

#### D1. Create Relay Operation Test Suite
**Priority: HIGH** ⭐⭐⭐
- [ ] Add tests for individual relay control (direction and enable separately)
- [ ] Test relay timing sequences (direction first, then enable)
- [ ] Validate relay state combinations for each motor operation
- [ ] Test emergency stop (immediate relay disable)
- [ ] Add relay state verification tests
- [ ] Test relay operation in both mock and hardware modes

#### D2. Enhance Hardware Integration Tests
**Priority: MEDIUM** ⭐⭐
- [ ] Extend existing hardware test sequencing with relay tests
- [ ] Add encoder validation tests with known rotation amounts
- [ ] Create home switch repeatability tests
- [ ] Add shutter timing validation tests
- [ ] Test non-blocking operation behavior
- [ ] Validate motor direction accuracy

#### D3. Create Comprehensive Motion Tests
**Priority: MEDIUM** ⭐⭐
- [ ] Test rotation accuracy over various distances
- [ ] Validate shortest-path rotation selection
- [ ] Test rapid start/stop sequences
- [ ] Verify encoder position tracking accuracy
- [ ] Test concurrent operation safety (prevent conflicting commands)
- [ ] Add performance timing tests

### 📖 E. Documentation and Safety

#### E1. Create Wiring Diagram Documentation
**Priority: MEDIUM** ⭐⭐
- [ ] Document K8055 to relay board connections
- [ ] Create relay to motor wiring diagrams
- [ ] Document limit switch wiring and logic
- [ ] Add encoder wiring and signal documentation
- [ ] Create troubleshooting guide for wiring issues
- [ ] Document safety considerations for each connection

#### E2. Enhance Operational Documentation
**Priority: MEDIUM** ⭐⭐
- [ ] Document non-blocking operation patterns
- [ ] Create motor control timing specifications
- [ ] Add encoder polling requirements documentation
- [ ] Document shutter operation safety procedures
- [ ] Create calibration procedures for new installations
- [ ] Add operational safety guidelines

#### E3. Create Debug and Diagnostic Tools
**Priority: LOW** ⭐
- [ ] Enhance `k8055_pin_tester.py` with relay testing modes
- [ ] Add real-time encoder monitoring tool
- [ ] Create relay state debugging utilities
- [ ] Add motor operation timing analysis tools
- [ ] Create automated hardware diagnosis script
- [ ] Add performance monitoring capabilities

### 🔧 F. Code Quality and Safety

#### F1. Add Safety Interlocks and Validation
**Priority: HIGH** ⭐⭐⭐
- [ ] Implement concurrent operation prevention
- [ ] Add motor enable state validation
- [ ] Create emergency stop validation
- [ ] Add relay state consistency checking
- [ ] Implement operation timeout safety
- [ ] Add hardware state validation before operations

#### F2. Improve Error Handling
**Priority: MEDIUM** ⭐⭐
- [ ] Add comprehensive error handling for relay operations
- [ ] Implement encoder error detection and recovery
- [ ] Add home switch failure detection
- [ ] Create motor stall detection (if possible)
- [ ] Improve timeout handling and user feedback
- [ ] Add hardware fault diagnosis

#### F3. Code Review and Optimization
**Priority: LOW** ⭐
- [ ] Review existing code for relay control patterns
- [ ] Optimize polling loops for performance
- [ ] Clean up debug output and logging
- [ ] Standardize error messages and status reporting
- [ ] Add comprehensive code documentation
- [ ] Remove deprecated or unused code

## 🏆 Success Criteria

### Phase 1 (High Priority Tasks)
- [x] Complete wiring connection table with all K8055 pins documented
- [x] Pin configuration validation with errors identified
- [x] Relay control logic analysis with critical issues documented
- [x] Non-blocking motor control implementation working
- [x] Bidirectional rotation working correctly
- [x] 2-bit Gray Code encoder reading implemented
- [x] Home switch polling optimized and reliable
- [x] Encoder calibration and validation system complete
- [ ] Basic relay operation test suite passing

### Phase 2 (Medium Priority Tasks)
- [ ] Shutter timing operations working reliably
- [ ] Encoder calibration and validation complete
- [ ] Hardware integration tests enhanced and passing
- [ ] Direction telemetry implemented (if hardware supports)
- [ ] Comprehensive documentation updated

### Phase 3 (Low Priority Tasks)
- [ ] Debug and diagnostic tools completed
- [ ] Performance monitoring implemented
- [ ] Code quality improvements finished
- [ ] All safety interlocks validated

## 📁 File Organization

**No new files unless absolutely necessary** - all work should enhance existing files:

### Core Files to Modify:
- `indi_driver/lib/dome.py` - Main motor control logic
- `indi_driver/lib/pyk8055_wrapper.py` - Hardware interface enhancements
- `indi_driver/dome_config.json` - Pin configuration validation
- `test/integration/` - Hardware integration tests
- `tools/k8055_pin_tester.py` - Enhanced testing capabilities

### Documentation to Update:
- `doc/Hardware_Test_Sequencing.md` - Add relay and encoder tests
- `doc/Troubleshooting_Guide.md` - Add wiring and motor control sections
- `doc/User_Guide.md` - Add operational guidance
- `README.md` files - Update with new capabilities

### Maintain Separation:
- `indi_driver/` folder remains "plug-out" standalone for real hardware
- All tests can switch between mock and hardware modes
- Driver scripts remain hardware-agnostic

---

**Last Updated:** November 4, 2025
**Status:** Ready for implementation
**Next Action:** Review and prioritize top 3 tasks for immediate work
