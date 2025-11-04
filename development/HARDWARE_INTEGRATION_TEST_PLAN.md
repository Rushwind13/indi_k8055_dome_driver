# Hardware Integration Test Plan
## INDI K8055 Dome Driver - First Physical Hardware Integration

**Date:** November 2, 2025
**Purpose:** Validate software readiness and perform complete hardware integration for dome control system
**Hardware:** Raspberry Pi with K8055 USB interface and physical dome hardware

---

## 🎯 Overview

This plan outlines the complete process for transitioning from development/mock mode to production hardware integration with physical dome operations. The plan focuses on using the existing INDI scripts as black boxes, leveraging the built-in hardware abstraction that automatically switches between mock and real hardware based on configuration.

**Key Principle:** All testing uses the production INDI scripts exactly as INDI would use them, ensuring complete end-to-end validation without bypassing any abstraction layers.

---

## 📋 Phase 1: Pre-Integration Software Validation

### 1.1 Development Environment Validation
**Objective:** Ensure all software components are ready for hardware deployment

**Prerequisites:**
- [ ] Code is committed and pushed to main branch
- [ ] All development work is complete
- [ ] CI/CD pipeline (if any) is passing

**Validation Steps:**
```bash
# 1. Clone fresh copy to simulate production deployment
cd /tmp
git clone https://github.com/Rushwind13/indi_k8055_dome_driver.git
cd indi_k8055_dome_driver

# 2. Setup virtual environment
./setup_venv.sh
source venv/bin/activate

# 3. Run complete test suite in smoke mode
python test/run_tests.py --all

# 4. Verify specific integration tests
python test/run_tests.py --integration-only
python test/run_tests.py --unit-only
python test/run_tests.py --doc-only

# 5. Test all INDI scripts in mock mode
python test/integration/test_indi_scripts.py

# 6. Validate BDD test suite
python test/run_tests.py --bdd-only --mode smoke
```

**Success Criteria:**
- [ ] All tests pass (100% success rate)
- [ ] No critical or high-severity lint issues
- [ ] All INDI scripts execute without errors in mock mode
- [ ] BDD tests complete successfully in smoke mode
- [ ] Documentation scripts execute correctly

**Estimated Time:** 30 minutes

### 1.2 Configuration Preparation
**Objective:** Prepare production configuration files

**Steps:**
```bash
# 1. Create production config from template
cp examples/dome_config_production.json indi_driver/dome_config.json

# 2. Review configuration settings
cat indi_driver/dome_config.json
```

**Manual Configuration Review:**
- [ ] Verify `"mock_mode": false` in hardware section
- [ ] Verify `"smoke_test": false` in testing section
- [ ] Note calibration values that need hardware tuning:
  - [ ] `home_position`: Will need physical calibration
  - [ ] `ticks_to_degrees`: Will need encoder calibration
  - [ ] Pin assignments match actual wiring
- [ ] Safety timeouts are appropriate for real hardware
- [ ] Device port matches K8055 connection

**Estimated Time:** 15 minutes

---

## 🚀 Phase 2: Raspberry Pi Deployment

### 2.1 Hardware Setup
**Objective:** Install and configure the Raspberry Pi environment

**Prerequisites:**
- [ ] Raspberry Pi with fresh OS installation
- [ ] Network connectivity established
- [ ] SSH access configured
- [ ] K8055 hardware available but not yet connected

**Steps:**
```bash
# On Raspberry Pi
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python and development tools
sudo apt install -y python3 python3-pip python3-venv git build-essential

# 3. Install K8055 system dependencies
sudo apt install -y libusb-dev swig python3-dev

# 4. Clone project repository
cd /home/pi
git clone https://github.com/Rushwind13/indi_k8055_dome_driver.git
cd indi_k8055_dome_driver

# 5. Setup virtual environment
./setup_venv.sh
source venv/bin/activate

# 6. Verify software installation
python test/run_tests.py --bdd-only --mode smoke
```

**Success Criteria:**
- [ ] Repository cloned successfully
- [ ] Virtual environment created and activated
- [ ] All dependencies installed without errors
- [ ] Smoke tests pass on Raspberry Pi
- [ ] System ready for K8055 library installation

**Estimated Time:** 45 minutes

### 2.2 K8055 Library Installation
**Objective:** Install libk8055 and Python bindings

**Steps:**
```bash
# 1. Install libk8055 dependencies
sudo apt install -y libk8055-dev

# 2. If libk8055-dev not available, build from source
git clone https://github.com/medved/libk8055.git /tmp/libk8055
cd /tmp/libk8055/src
make
sudo make install

# 3. Build Python bindings
cd /tmp/libk8055/src/pyk8055
python3 setup.py build_ext --inplace
sudo python3 setup.py install

# 4. Test K8055 library availability
make check-k8055

# 5. Return to project directory
cd /home/pi/indi_k8055_dome_driver
```

**Success Criteria:**
- [ ] libk8055 library installed successfully
- [ ] Python bindings available
- [ ] No import errors when importing pyk8055
- [ ] Library can be imported from project virtual environment

**Estimated Time:** 30 minutes

### 2.3 Hardware Detection Validation
**Objective:** Verify the system correctly identifies hardware vs mock mode

**Steps:**
```bash
# 1. Create production configuration
cp examples/dome_config_production.json indi_driver/dome_config.json

# 2. Test hardware detection via INDI scripts (without hardware connected)
cd /home/pi/indi_k8055_dome_driver/indi_driver/scripts
python3 connect.py
echo "Connect exit code (should be 1 - no hardware): $?"

# 3. Verify scripts handle missing hardware gracefully
python3 status.py
echo "Status exit code (should be 1 - no hardware): $?"
```

**Success Criteria:**
- [ ] Scripts fail gracefully when hardware not available (exit code 1)
- [ ] Configuration loaded correctly from production config
- [ ] No crashes or unexpected errors, just clean failure modes
- [ ] System ready for hardware connection

**Estimated Time:** 10 minutes

---

## 🔧 Phase 3: Hardware Integration Testing

### 3.1 Initial Hardware Connection
**Objective:** Connect K8055 and verify basic communication via existing test framework

**Prerequisites:**
- [ ] K8055 board available
- [ ] USB cable
- [ ] Power supply for K8055 if required
- [ ] No dome motors connected yet (safety)

**Steps:**
```bash
# 1. Connect K8055 to Raspberry Pi USB
# 2. Check USB device recognition
lsusb | grep -i velleman

# 3. Test hardware connection via existing integration tests
cd /home/pi/indi_k8055_dome_driver

# Run integration test suite - will validate all INDI scripts
python test/integration/test_indi_scripts.py

# Check specific connection validation using helper script
make hardware-test-connect

# 4. Test wrapper integration with hardware mode
python test/integration/test_wrapper_integration.py
```

**Success Criteria:**
- [ ] K8055 device detected by USB subsystem
- [ ] test_indi_scripts.py passes all connection tests
- [ ] test_wrapper_integration.py passes in hardware mode
- [ ] No communication timeouts or crashes
- [ ] All existing test validations pass

**Rollback Trigger:** If integration tests fail, return to mock mode for debugging

**Estimated Time:** 15 minutes

### 3.2 Sensor Validation (No Motors)
**Objective:** Test all sensors using existing test framework validation

**Prerequisites:**
- [ ] K8055 connected and communicating
- [ ] Dome sensors connected to K8055 inputs
- [ ] NO motor power connected yet

**Steps:**
```bash
cd /home/pi/indi_k8055_dome_driver

# 1. Use existing test framework to validate sensor functionality
# The test_status_script_output_format test validates sensor data format
make hardware-test-status

# 2. Capture baseline readings for documentation
python3 indi_driver/scripts/status.py > baseline_status.txt
echo "Baseline sensor reading: $(cat baseline_status.txt)"

# 3. Test home switch activation manually
echo "Manually activate home switch and press Enter to test sensor response..."
read
python3 indi_driver/scripts/status.py > home_active_status.txt
echo "Home active reading: $(cat home_active_status.txt)"

echo "Release home switch and press Enter..."
read
python3 indi_driver/scripts/status.py > home_released_status.txt
echo "Home released reading: $(cat home_released_status.txt)"

# 4. Document sensor validation results
echo "=== SENSOR VALIDATION SUMMARY ===" > sensor_validation.log
echo "Baseline:     $(cat baseline_status.txt)" >> sensor_validation.log
echo "Home Active:  $(cat home_active_status.txt)" >> sensor_validation.log
echo "Home Released:$(cat home_released_status.txt)" >> sensor_validation.log
echo "Test completed: $(date)" >> sensor_validation.log
```

**Success Criteria:**
- [ ] test_status_script_output_format passes with hardware
- [ ] Status output format: "parked_boolean shutter_boolean azimuth_float"
- [ ] Home switch activation visible in status changes
- [ ] All values within valid ranges (azimuth 0-360, booleans true/false)
- [ ] Sensor responses are reliable and repeatable

**Rollback Trigger:** If status format validation fails or sensors don't respond correctly

**Estimated Time:** 20 minutes

### 3.3 Motor Connection and Initial Tests
**Objective:** Connect motors and test basic movement using existing test framework

**Prerequisites:**
- [ ] All sensors validated via existing tests
- [ ] Motor power supplies available
- [ ] Emergency stop procedures ready
- [ ] Physical safety measures in place

**⚠️ SAFETY REQUIREMENTS:**
- [ ] Dome area clear of personnel
- [ ] Emergency stop button accessible
- [ ] Manual motor disconnects ready
- [ ] Dome mechanically free to move
- [ ] Observer positioned safely outside dome rotation area

**Steps:**
```bash
cd /home/pi/indi_k8055_dome_driver

# 1. Connect motor power but keep motors disabled initially
# 2. Test connection still works with motors connected via existing tests
python test/integration/test_indi_scripts.py::TestINDIScripts::test_connect_script

# 3. Test movement scripts using existing validation
echo "⚠️  STARTING MOTOR TESTS - BE READY TO EMERGENCY STOP"
python test/integration/test_indi_scripts.py::TestINDIScripts::test_movement_scripts

# 4. Test abort functionality
python test/integration/test_indi_scripts.py::TestINDIScripts::test_abort_script

# 5. Run full INDI compliance test
python test/integration/test_indi_scripts.py::TestINDIScripts::test_indi_contract_compliance
```

**Success Criteria:**
- [ ] test_connect_script passes with motors connected
- [ ] test_movement_scripts passes (tests move_cw.py, move_ccw.py, abort.py)
- [ ] test_abort_script validates emergency stop functionality
- [ ] test_indi_contract_compliance ensures all scripts return proper exit codes
- [ ] No runaway motors or unsafe behavior

**Rollback Triggers:**
- Any existing test fails
- Motors don't stop when abort is tested
- Any unsafe behavior observed

**Estimated Time:** 25 minutes

---

## 🧪 Phase 4: Smoke Testing with Hardware

### 4.1 Basic Movement Tests
**Objective:** Test dome functions using existing BDD and integration test framework

**Prerequisites:**
- [ ] Motor control validated via existing tests
- [ ] Emergency stops tested
- [ ] All safety measures in place

**Steps:**
```bash
cd /home/pi/indi_k8055_dome_driver

# 1. Run existing BDD hardware tests
export DOME_TEST_MODE=hardware

# Test startup/shutdown using existing BDD framework
python test/run_tests.py --feature dome_startup_shutdown --mode hardware --yes

# Test rotation using existing BDD framework
python test/run_tests.py --feature dome_rotation --mode hardware --yes

# Test home operations using existing BDD framework
python test/run_tests.py --feature dome_home --mode hardware --yes

# 2. Run existing INDI script integration tests
python test/integration/test_indi_scripts.py

# 3. Run existing wrapper integration tests
python test/integration/test_wrapper_integration.py
```

**Success Criteria:**
- [ ] dome_startup_shutdown BDD tests pass in hardware mode
- [ ] dome_rotation BDD tests pass in hardware mode
- [ ] dome_home BDD tests pass in hardware mode
- [ ] All test_indi_scripts.py tests pass
- [ ] test_wrapper_integration.py passes in hardware mode
- [ ] No hardware timeouts or communication errors

**Critical Monitoring:**
- [ ] Watch for overheating
- [ ] Monitor for unusual noises
- [ ] Verify smooth operation
- [ ] Ensure emergency stop is always effective

**Estimated Time:** 30 minutes

### 4.2 Calibration and Configuration Tuning
**Objective:** Use existing tests to validate dome calibration and accuracy

**Steps:**
```bash
cd /home/pi/indi_k8055_dome_driver

# 1. Run existing park/home tests to validate home position
python test/integration/test_indi_scripts.py::TestINDIScripts::test_park_script

# 2. Run existing goto tests to validate positioning accuracy
python test/integration/test_indi_scripts.py::TestINDIScripts::test_goto_script

# 3. Run dome rotation BDD tests which include positioning validation
export DOME_TEST_MODE=hardware
python test/run_tests.py --feature dome_rotation --mode hardware --yes

# 4. Run dome home BDD tests which validate home finding
python test/run_tests.py --feature dome_home --mode hardware --yes

# 5. Test positioning accuracy with existing validation
# The dome_rotation.feature includes tests for:
# - Rotate to specific azimuth
# - Wraparound handling
# - Shortest path calculation
# - Position accuracy validation

echo "Calibration validation complete via existing test framework"
```

**Success Criteria:**
- [ ] test_park_script passes (validates home operation)
- [ ] test_goto_script passes (validates positioning commands)
- [ ] dome_rotation BDD tests pass (validates accuracy and wraparound)
- [ ] dome_home BDD tests pass (validates home finding reliability)
- [ ] All positioning tests within acceptable tolerance

**Manual Configuration Update Required:**
- If BDD tests fail due to calibration issues, update `examples/dome_config_production.json`
- Use test results to identify needed adjustments to `home_position` or `ticks_to_degrees`

**Estimated Time:** 45 minutes

---

## 🎯 Phase 5: INDI Integration and Acceptance Testing

### 5.1 INDI Script Validation
**Objective:** Use existing integration tests to validate all INDI scripts with hardware

**Prerequisites:**
- [ ] Dome calibrated and operating correctly
- [ ] Configuration tuned for hardware
- [ ] All basic functions validated

**Steps:**
```bash
cd /home/pi/indi_k8055_dome_driver

# 1. Run complete INDI script integration test suite
python test/integration/test_indi_scripts.py

# This test suite includes:
# - test_all_scripts_exist: Validates all 11 scripts are present
# - test_all_scripts_executable: Validates scripts are executable
# - test_connect_script: Tests hardware connection
# - test_disconnect_script: Tests clean shutdown
# - test_status_script_output_format: Validates status format
# - test_shutter_scripts: Tests open/close operations
# - test_park_script: Tests park operation
# - test_unpark_script: Tests unpark operation
# - test_goto_script: Tests goto positioning
# - test_movement_scripts: Tests CW/CCW movement and abort
# - test_abort_script: Tests emergency stop
# - test_script_error_handling: Tests graceful error handling
# - test_indi_contract_compliance: Tests INDI contract compliance

echo "INDI script validation complete via existing test framework"
```

**Success Criteria:**
- [ ] All tests in test_indi_scripts.py pass
- [ ] test_connect_script establishes hardware communication
- [ ] test_status_script_output_format validates proper format
- [ ] test_movement_scripts validates rotation in both directions
- [ ] test_abort_script confirms emergency stop works
- [ ] test_indi_contract_compliance confirms proper exit codes

**Estimated Time:** 30 minutes

### 5.2 Shutter System Testing (if available)
**Objective:** Test shutter operations using existing test framework

**Prerequisites:**
- [ ] Shutter motor connected
- [ ] Limit switches functional
- [ ] Safety systems operational

**Steps:**
```bash
cd /home/pi/indi_k8055_dome_driver

# 1. Run existing shutter tests
python test/integration/test_indi_scripts.py::TestINDIScripts::test_shutter_scripts

# 2. Run shutter-specific BDD tests
export DOME_TEST_MODE=hardware
python test/run_tests.py --feature shutter_operations --mode hardware --yes

# The existing test framework includes:
# - test_shutter_scripts: Tests open.py and close.py scripts
# - shutter_operations.feature: BDD tests for shutter functionality
```

**Success Criteria (if applicable):**
- [ ] test_shutter_scripts passes (validates open/close operations)
- [ ] shutter_operations BDD tests pass in hardware mode
- [ ] Limit switches prevent over-travel
- [ ] Shutter operations complete within timeout
- [ ] Status correctly reflects shutter position

**Estimated Time:** 20 minutes (if applicable)

### 5.3 Integration with Ekos/INDI
**Objective:** Configure dome in INDI/Ekos for operational use

**Prerequisites:**
- [ ] INDI server installed on Raspberry Pi
- [ ] Ekos client available (can be remote)
- [ ] All individual scripts tested and working

**Steps:**
```bash
# 1. Install INDI server if not present
sudo apt install -y indi-bin

# 2. Test INDI dome_script driver configuration
# Create INDI driver configuration using helper
make hardware-indi-config

# 3. Start INDI server with dome_script driver
indiserver -v indi_dome_script &
INDI_PID=$!

# 4. Test INDI connection from client
# This would typically be done from Ekos or INDI client
sleep 5
kill $INDI_PID
```

**Manual Ekos Integration:**
1. **Connect to INDI Server:**
   - Open Ekos
   - Add equipment profile for dome
   - Set INDI server to Raspberry Pi IP address
   - Configure dome_script driver

2. **Configure Dome Scripts:**
   - Set script folder: `/home/pi/indi_k8055_dome_driver/indi_driver/scripts`
   - Configure script names as listed in project README
   - Test connection

3. **Functional Testing:**
   - [ ] Connect to dome from Ekos
   - [ ] Test park/unpark operations
   - [ ] Test goto azimuth commands
   - [ ] Test rotation controls
   - [ ] Test abort functionality
   - [ ] Verify status updates

**Success Criteria:**
- [ ] INDI server recognizes dome_script driver
- [ ] Ekos can connect to dome
- [ ] All dome operations available in Ekos interface
- [ ] Status updates correctly in real-time
- [ ] Commands execute reliably
- [ ] Error conditions handled gracefully

**Estimated Time:** 45 minutes

---

## 🔄 Phase 6: Comprehensive Acceptance Testing

### 6.1 Full System BDD Test Suite
**Objective:** Run complete BDD test suite with hardware

**Prerequisites:**
- [ ] All individual components tested
- [ ] INDI integration validated
- [ ] System operating reliably

**Steps:**
```bash
# 1. Run complete hardware test suite
cd /home/pi/indi_k8055_dome_driver
export DOME_TEST_MODE=hardware

# 2. Execute all BDD features
python test/run_tests.py --mode hardware --yes

# 3. Document results
python test/run_tests.py --mode hardware --format json --output acceptance_test_results.json --yes

# 4. Verify critical functions
python test/run_tests.py --tag @critical --mode hardware --yes

# 5. Test error handling scenarios
python test/run_tests.py --feature error_handling --mode hardware --yes
```

**Success Criteria:**
- [ ] All BDD scenarios pass (>95% success rate acceptable)
- [ ] Critical scenarios have 100% success rate
- [ ] Error handling scenarios respond appropriately
- [ ] No safety-critical failures
- [ ] Performance within acceptable parameters

**Estimated Time:** 90 minutes

### 6.2 Stress and Endurance Testing
**Objective:** Use existing test framework for extended operation validation

**Steps:**
```bash
cd /home/pi/indi_k8055_dome_driver

# 1. Run existing integration tests multiple times for endurance
echo "=== ENDURANCE TEST: REPEATED INTEGRATION TESTS ==="
export DOME_TEST_MODE=hardware

for i in {1..10}; do
    echo "Endurance iteration $i/10"

    # Run goto tests (includes position accuracy validation)
    python test/integration/test_indi_scripts.py::TestINDIScripts::test_goto_script

    # Run movement tests (includes CW/CCW and abort)
    python test/integration/test_indi_scripts.py::TestINDIScripts::test_movement_scripts

    # Brief pause between iterations
    sleep 2
done

# 2. Run BDD rotation tests for extended validation
echo "=== ROTATION ENDURANCE TEST ==="
python test/run_tests.py --feature dome_rotation --mode hardware --yes

# 3. Run error handling tests
echo "=== ERROR HANDLING TEST ==="
python test/run_tests.py --feature error_handling --mode hardware --yes

echo "Endurance testing complete via existing test framework"
```

**Success Criteria:**
- [ ] Integration tests pass consistently across multiple iterations (>90% success rate)
- [ ] test_goto_script validates positioning accuracy repeatedly
- [ ] test_movement_scripts confirms reliable start/stop operation
- [ ] dome_rotation BDD tests pass for extended operations
- [ ] error_handling tests validate graceful failure modes
- [ ] No degradation in performance over time

**Estimated Time:** 45 minutes

---

## 🚨 Rollback and Emergency Procedures

### Immediate Emergency Rollback
**If ANY safety issue occurs:**

```bash
# 1. IMMEDIATE STOP via existing abort script
cd /home/pi/indi_k8055_dome_driver/indi_driver/scripts
python3 abort.py

# 2. Switch to mock mode
cd /home/pi/indi_k8055_dome_driver
cp examples/dome_config_development.json indi_driver/dome_config.json

# 3. Verify mock mode operation via existing tests
python test/run_tests.py --mode smoke

# 4. Test that existing framework now runs in mock mode
python test/integration/test_indi_scripts.py::TestINDIScripts::test_connect_script

# 5. Document issue and halt hardware testing
echo "$(date): EMERGENCY ROLLBACK - $(reason)" >> emergency_log.txt
```

### Planned Rollback Scenarios

#### Scenario 1: K8055 Communication Issues
```bash
# Symptoms: Device timeouts, connection errors from existing tests
# 1. Return to mock mode
cd /home/pi/indi_k8055_dome_driver
cp examples/dome_config_development.json indi_driver/dome_config.json

# 2. Verify mock mode works via existing test framework
python test/integration/test_indi_scripts.py::TestINDIScripts::test_connect_script

# 3. Debug hardware connection
lsusb | grep -i velleman
dmesg | tail -20

# 4. Test return to hardware mode
cp examples/dome_config_production.json indi_driver/dome_config.json
python test/integration/test_indi_scripts.py::TestINDIScripts::test_connect_script
```

#### Scenario 2: Calibration Problems
```bash
# Symptoms: BDD tests fail, positioning accuracy poor
# 1. Revert to default calibration values
cd /home/pi/indi_k8055_dome_driver
cp examples/dome_config_production.json indi_driver/dome_config.json
echo "Reverted to default calibration values"

# 2. Test with default values using existing framework
python test/integration/test_indi_scripts.py::TestINDIScripts::test_park_script

# 3. Run focused test on positioning
export DOME_TEST_MODE=hardware
python test/run_tests.py --feature dome_home --mode hardware --yes
```

#### Scenario 3: INDI Integration Failure
```bash
# Symptoms: Existing tests fail, INDI can't connect
# 1. Test all scripts via existing test framework
cd /home/pi/indi_k8055_dome_driver
python test/integration/test_indi_scripts.py --verbose

# 2. Revert to working configuration
git checkout HEAD -- indi_driver/dome_config.json

# 3. Test basic functionality with reverted config
python test/integration/test_indi_scripts.py::TestINDIScripts::test_connect_script

# 4. Run full integration test suite
python test/integration/test_indi_scripts.py
```

---

## 📊 Success Metrics and Acceptance Criteria

### Critical Success Criteria (Must Pass)
- [ ] **Safety:** No unsafe conditions or runaway operations
- [ ] **Accuracy:** Position accuracy within ±2 degrees
- [ ] **Reliability:** >98% command success rate
- [ ] **Responsiveness:** Commands complete within expected timeouts
- [ ] **INDI Compliance:** All INDI scripts return correct exit codes and output

### Performance Benchmarks
- [ ] **Rotation Speed:** Full 360° rotation in <300 seconds
- [ ] **Positioning Accuracy:** ±1 degree for goto commands
- [ ] **Home Repeatability:** Home position within ±0.5 degrees
- [ ] **Command Response:** Commands acknowledged within 2 seconds
- [ ] **Status Updates:** Position updates within 1 second

### Functional Requirements
- [ ] **Basic Operations:** All dome movements work correctly
- [ ] **Home Function:** Reliable home finding and return
- [ ] **Safety Systems:** Emergency stop effective in <1 second
- [ ] **Error Handling:** Graceful handling of error conditions
- [ ] **Configuration:** Production config properly applied

---

## 📋 Test Documentation and Deliverables

### Required Documentation
1. **Test Execution Log** - Complete record of all test steps and results
2. **Hardware Configuration** - Final calibrated dome_config.json
3. **Performance Metrics** - Measured accuracy and timing data
4. **Issue Log** - Any problems encountered and resolutions
5. **Acceptance Sign-off** - Formal acceptance of hardware integration

### Configuration Backup
```bash
# Create backup of working configuration
cp indi_driver/dome_config.json dome_config_production_validated_$(date +%Y%m%d).json

# Create system information snapshot using helper script
make hardware-sysinfo
```

---

## 🔧 Production Readiness Prerequisites

Before executing this hardware integration test plan, complete the code changes outlined in **`PRODUCTION_READINESS_TASKS.md`**. These changes ensure the existing test framework operates correctly with real hardware.

**Key Areas Requiring Updates:**
- Test framework hardware mode support and timeout adjustments
- Safety integration and error recovery mechanisms
- Hardware-specific test assertions and validation
- Configuration validation for production mode

**Status:** 📋 Refer to `PRODUCTION_READINESS_TASKS.md` for detailed implementation tasks and tracking.

---

## ⏱️ Total Time Estimate

| Phase | Estimated Time |
|-------|----------------|
| Phase 1: Software Validation | 45 minutes |
| Phase 2: Raspberry Pi Deployment | 85 minutes |
| Phase 3: Hardware Integration | 60 minutes |
| Phase 4: Smoke Testing | 75 minutes |
| Phase 5: INDI Integration | 95 minutes |
| Phase 6: Acceptance Testing | 135 minutes |
| **Total** | **8 hours** |

**Recommended Schedule:**
- **Day 1:** Phases 1-3 (Software validation and basic hardware integration) - 3.5 hours
- **Day 2:** Phases 4-6 (Testing and INDI integration) - 4.5 hours

**Key Benefits of INDI Script Approach:**
- Tests the exact same interface that INDI will use
- No bypassing of abstraction layers
- Automatic mock/hardware mode switching via configuration
- Validates complete end-to-end functionality
- Simpler rollback procedures (just configuration changes)

---

## 🔗 Quick Reference Commands

### Essential Testing Commands
```bash
# Check K8055 hardware availability
make check-k8055

# Test hardware connection
make hardware-test-connect

# Test status script format
make hardware-test-status

# Setup INDI configuration
make hardware-indi-config

# Create system information snapshot
make hardware-sysinfo

# Run all hardware helper tests
make hardware-test-all

# Smoke test everything via existing framework
python test/run_tests.py --all

# Hardware test specific feature via existing BDD tests
python test/run_tests.py --feature dome_rotation --mode hardware --yes

# Test INDI scripts via existing integration tests
python test/integration/test_indi_scripts.py

# Emergency stop via existing abort script
cd indi_driver/scripts && python3 abort.py

# Switch to mock mode and verify via existing tests
cp examples/dome_config_development.json indi_driver/dome_config.json
python test/integration/test_indi_scripts.py::TestINDIScripts::test_connect_script

# Switch to hardware mode and verify via existing tests
cp examples/dome_config_production.json indi_driver/dome_config.json
python test/integration/test_indi_scripts.py::TestINDIScripts::test_connect_script
```

### Configuration Files
- **Mock Mode:** `examples/dome_config_development.json`
- **Hardware Mode:** `examples/dome_config_production.json`
- **Active Config:** `indi_driver/dome_config.json`

### Key Safety Notes
- ⚠️ **Always test in smoke mode first**
- ⚠️ **Have emergency stop procedures ready**
- ⚠️ **Never leave hardware tests unattended**
- ⚠️ **Verify safety systems before motor connection**
- ⚠️ **Clear dome area of personnel during testing**

---

*This plan ensures comprehensive validation while maintaining safety throughout the hardware integration process. Each phase builds upon the previous one, with clear rollback procedures if any issues arise.*
