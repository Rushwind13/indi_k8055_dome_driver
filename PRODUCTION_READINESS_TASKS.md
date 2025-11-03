# Production Readiness Tasks
## INDI K8055 Dome Driver - Hardware Mode Enhancements

**Date:** November 2, 2025
**Purpose:** Code changes required to transition existing test framework for production hardware integration
**Priority:** Complete before first hardware integration testing

---

## 🎯 Overview

Based on leveraging the existing test framework for hardware integration, the following changes are needed to ensure the test suite operates correctly with real hardware. Most of the existing test framework should work with hardware mode via configuration changes. The primary requirement is ensuring timeouts and expectations are appropriate for real hardware operation.

---

## 🔧 Required Code Changes

### 1. Test Framework Hardware Mode Support
**Current:** Tests run in mock mode by default
**Required:** Better hardware mode detection and configuration

**Files to Modify:**
- `test/integration/features/environment.py`
- `test/run_tests.py`
- `test/integration/test_indi_scripts.py`

**Changes Needed:**
- [ ] Ensure `DOME_TEST_MODE=hardware` properly configures all tests for hardware operation
- [ ] Verify existing BDD environment.py correctly switches between mock/hardware modes
- [ ] Add validation that hardware tests have appropriate timeouts for real operations
- [ ] Add configuration validation to ensure hardware mode is properly detected

**Implementation Notes:**
- Check environment variable handling in BDD setup
- Verify test configuration loading respects hardware mode
- Add debug logging to confirm mode detection

### 2. Integration Test Timeout Adjustments
**Current:** Some tests have short timeouts suitable for mock mode
**Required:** Hardware-appropriate timeouts

**Files to Modify:**
- `test/integration/test_indi_scripts.py`
- `test/integration/features/*.feature` files
- `test/integration/features/steps/*.py` step files

**Changes Needed:**
- [ ] Increase timeout for `test_park_script` and `test_goto_script` for real hardware movement
- [ ] Adjust BDD step timeouts in features/*.feature files for hardware operations
- [ ] Ensure `test_movement_scripts` allows sufficient time for real rotation
- [ ] Add hardware-specific timeout configuration

**Implementation Notes:**
- Mock operations: ~1-2 second timeouts
- Hardware operations: 30-120 second timeouts for movement
- Consider dome size and motor speed in timeout calculations

### 3. Configuration Validation in Tests
**Current:** Tests assume configuration is valid
**Required:** Validate production configuration before hardware tests

**Files to Modify:**
- `test/integration/test_indi_scripts.py`
- New file: `test/integration/test_config_validation.py`

**Changes Needed:**
- [ ] Add config validation test that checks hardware mode settings
- [ ] Verify pin assignments are valid before running hardware tests
- [ ] Add test to confirm calibration values are reasonable
- [ ] Validate hardware configuration completeness

**Implementation Notes:**
- Check `mock_mode: false` in hardware configuration
- Validate pin assignments are within K8055 valid ranges
- Check that calibration values are non-zero and reasonable

### 4. Error Recovery in Test Framework
**Current:** Tests may not handle hardware failures gracefully
**Required:** Robust error handling for hardware mode

**Files to Modify:**
- `test/integration/test_indi_scripts.py`
- `test/integration/features/steps/*.py`
- `test/integration/features/environment.py`

**Changes Needed:**
- [ ] Ensure tests can recover from hardware communication failures
- [ ] Add cleanup in test teardown to return dome to safe state
- [ ] Implement test-level abort functionality for safety
- [ ] Add retry logic for transient hardware failures

**Implementation Notes:**
- Call abort.py in test teardown if hardware tests fail
- Implement graceful degradation for communication timeouts
- Add hardware state reset between test runs

### 5. Hardware-Specific Test Assertions
**Current:** Some tests may have mock-mode expectations
**Required:** Hardware-appropriate validation

**Files to Modify:**
- `test/integration/features/dome_rotation.feature`
- `test/integration/features/dome_home.feature`
- `test/integration/features/shutter_operations.feature`
- `test/integration/features/steps/*.py`

**Changes Needed:**
- [ ] Review position accuracy tolerances in BDD tests for hardware reality
- [ ] Adjust timing expectations in dome_rotation.feature for real motors
- [ ] Update shutter_operations.feature for actual limit switch behavior
- [ ] Modify assertions to account for mechanical tolerances

**Implementation Notes:**
- Mock mode: Perfect positioning (±0.1°)
- Hardware mode: Realistic tolerances (±1-2°)
- Account for mechanical backlash and encoder resolution

### 6. Test Data Capture for Calibration
**Current:** Tests validate but don't capture calibration data
**Required:** Tests that help with hardware calibration

**Files to Create:**
- `test/integration/test_calibration_helpers.py`
- `test/tools/calibration_data_capture.py`

**Changes Needed:**
- [ ] Add test methods to capture actual vs expected positions for calibration
- [ ] Create test that measures actual rotation speed for timeout tuning
- [ ] Add test to capture home position repeatability data
- [ ] Implement calibration data logging and analysis

**Implementation Notes:**
- Log position accuracy over multiple goto operations
- Measure rotation timing for timeout calibration
- Capture home position variance for repeatability analysis

### 7. Production Test Sequencing
**Current:** Tests can run in any order
**Required:** Hardware tests may need specific sequencing

**Files to Modify:**
- `test/integration/test_indi_scripts.py`
- `test/run_tests.py`
- Add: `test/integration/test_hardware_sequencing.py`

**Changes Needed:**
- [ ] Ensure hardware tests don't interfere with each other
- [ ] Add test dependencies where needed (e.g., home before goto)
- [ ] Implement proper test isolation for hardware mode
- [ ] Add test ordering for hardware safety

**Implementation Notes:**
- Hardware tests should start with dome in known state
- Implement test fixtures for hardware state management
- Add markers for hardware-dependent test ordering

### 8. Safety Integration in Test Framework
**Current:** Tests assume safe operation
**Required:** Safety checks integrated into test flow

**Files to Modify:**
- `test/integration/features/environment.py`
- `test/integration/test_indi_scripts.py`
- Add: `test/integration/test_safety_systems.py`

**Changes Needed:**
- [ ] Add pre-test safety validation
- [ ] Integrate abort functionality into test teardown
- [ ] Add test timeout safety mechanisms
- [ ] Implement emergency stop testing

**Implementation Notes:**
- Validate abort.py functionality before motor tests
- Add safety timeouts to prevent runaway operations
- Test emergency stop response times

---

## 🏗️ Implementation Plan

### Phase 1: Core Infrastructure (Priority: High)
1. **Test Framework Hardware Mode Support** - Essential for all hardware testing
2. **Integration Test Timeout Adjustments** - Required for reliable hardware testing
3. **Safety Integration** - Critical for safe hardware operation

### Phase 2: Enhanced Validation (Priority: Medium)
4. **Configuration Validation** - Important for reliable setup
5. **Error Recovery** - Improves test reliability
6. **Hardware-Specific Assertions** - Better test accuracy

### Phase 3: Advanced Features (Priority: Low)
7. **Test Data Capture** - Helpful for calibration
8. **Production Test Sequencing** - Optimization for hardware testing

---

## ✅ Acceptance Criteria

Each task should meet the following criteria:

### Functional Requirements
- [ ] **Backward Compatibility:** Changes don't break existing mock mode testing
- [ ] **Hardware Safety:** All changes include appropriate safety mechanisms
- [ ] **Error Handling:** Graceful failure modes for hardware communication issues
- [ ] **Documentation:** All changes are properly documented

### Testing Requirements
- [ ] **Unit Tests:** New functionality has unit test coverage
- [ ] **Integration Tests:** Changes work with existing integration test suite
- [ ] **BDD Tests:** Hardware mode works with all BDD scenarios
- [ ] **Mock Mode:** All changes maintain mock mode functionality

### Performance Requirements
- [ ] **Timeout Handling:** Appropriate timeouts for hardware operations
- [ ] **Resource Management:** Proper cleanup of hardware connections
- [ ] **Reliability:** Tests pass consistently with hardware (>95% success rate)

---

## 📋 Task Tracking

Use this checklist to track implementation progress:

### Infrastructure Tasks
- [ ] Task 1: Test Framework Hardware Mode Support
- [ ] Task 2: Integration Test Timeout Adjustments
- [ ] Task 8: Safety Integration in Test Framework

### Validation Tasks
- [ ] Task 3: Configuration Validation in Tests
- [ ] Task 4: Error Recovery in Test Framework
- [ ] Task 5: Hardware-Specific Test Assertions

### Enhancement Tasks
- [ ] Task 6: Test Data Capture for Calibration
- [ ] Task 7: Production Test Sequencing

### Validation Checklist
- [ ] All tasks pass unit tests
- [ ] All tasks pass integration tests
- [ ] All tasks pass BDD tests in mock mode
- [ ] All tasks ready for hardware mode testing
- [ ] Documentation updated
- [ ] Code reviewed and approved

---

## 🔗 Related Files

### Test Framework Files
- `test/run_tests.py` - Main test runner
- `test/integration/test_indi_scripts.py` - INDI script integration tests
- `test/integration/test_wrapper_integration.py` - Hardware wrapper tests

### BDD Framework Files
- `test/integration/features/environment.py` - BDD test setup
- `test/integration/features/*.feature` - BDD test scenarios
- `test/integration/features/steps/*.py` - BDD step implementations

### Configuration Files
- `examples/dome_config_production.json` - Hardware configuration template
- `examples/dome_config_development.json` - Mock configuration template

### Helper Scripts
- `hardware_test_helper.py` - Hardware testing utilities
- `Makefile` - Build and test targets

---

*This document tracks all code changes needed to make the existing test framework ready for production hardware integration. Complete these tasks before proceeding with the Hardware Integration Test Plan.*
