# Dome Control System - BDD Test Suite

This directory contains a comprehensive Behavior-Driven Development (BDD) test suite for the dome control system. The tests are written using Cucumber/Gherkin syntax and executed with the Python `behave` framework.

## 🔍 Overview

The test suite provides comprehensive coverage of dome operations including:
- **Startup and Shutdown**: System initialization and safe shutdown procedures
- **Dome Rotation**: Clockwise/counter-clockwise rotation and azimuth positioning
- **Home Operations**: Finding and returning to home position
- **Shutter Control**: Opening and closing shutter with safety checks
- **Telemetry Monitoring**: Position reporting and system status
- **Error Handling**: Edge cases, hardware failures, and safety scenarios

## 🔧 Test Modes

### Smoke Test Mode (Default)
- **Safe**: No real hardware operations
- **Fast**: Quick execution with simulated responses
- **Development**: Perfect for development and CI/CD
- **Verification**: Validates logic without physical risk

### Hardware Test Mode
- **Real Operations**: Actual dome and shutter movements
- **Hardware Required**: Must have properly configured dome system
- **Safety Critical**: Requires proper setup and precautions
- **Full Integration**: Complete end-to-end testing

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Install test dependencies
pip install -r test/requirements.txt

# Or install manually
pip install behave mock
```

### 2. Run Smoke Tests (Safe)
```bash
# Run all smoke tests
python test/run_tests.py

# Run specific feature
python test/run_tests.py --feature rotation

# List available features
python test/run_tests.py --list-features
```

### 3. Run Hardware Tests (CAUTION!)
```bash
# ⚠️ WARNING: This operates real hardware!
python test/run_tests.py --mode hardware
```

## 📋 Test Features

### `dome_startup_shutdown.feature`
Tests system initialization and shutdown procedures:
- Power on sequence
- Subsystem initialization
- Graceful shutdown
- Emergency shutdown
- Startup timeout handling

### `dome_rotation.feature`
Tests dome rotation operations:
- Clockwise and counter-clockwise rotation
- Specific degree movements
- Azimuth slewing
- Rotation boundaries and limits

### `dome_home.feature`
Tests home position operations:
- Finding home position
- Returning to home
- Home position accuracy
- Home sensor validation

### `shutter_operations.feature`
Tests shutter control:
- Opening and closing operations
- Safety interlocks
- Timeout protection
- Status verification

### `telemetry_monitoring.feature`
Tests monitoring and reporting:
- Position reporting
- Status monitoring
- Telemetry accuracy
- Data consistency

### `error_handling.feature`
Tests error conditions and edge cases:
- Hardware communication timeouts
- Encoder malfunctions
- Motor stall detection
- Power supply issues
- Emergency procedures

## 🎯 Running Specific Tests

### By Feature
```bash
# Run rotation tests only
python test/run_tests.py --feature rotation

# Run error handling tests
python test/run_tests.py --feature error_handling
```

### By Tag (if implemented)
```bash
# Run critical tests only
python test/run_tests.py --tag @critical

# Run smoke tests only
python test/run_tests.py --tag @smoke
```

### With Different Output Formats
```bash
# JSON output for CI/CD
python test/run_tests.py --format json --output results.json

# JUnit XML for integration
python test/run_tests.py --format junit --output results.xml
```

## 🛡️ Safety Considerations

### Hardware Test Mode Safety
- ⚠️ **Physical Safety**: Ensure dome area is clear of personnel
- ⚠️ **Equipment Safety**: Verify dome is mechanically sound
- ⚠️ **Configuration**: Check all settings and limits
- ⚠️ **Emergency Stop**: Have emergency stop readily available
- ⚠️ **Supervision**: Never run hardware tests unattended

### Safe Testing Practices
1. **Always start with smoke tests** to verify logic
2. **Use hardware mode only when necessary** for final validation
3. **Have safety procedures** in place before hardware testing
4. **Monitor hardware tests** continuously
5. **Stop immediately** if anything seems wrong

## 📁 Directory Structure

```
test/
├── features/                    # Cucumber feature files
│   ├── dome_startup_shutdown.feature
│   ├── dome_rotation.feature
│   ├── dome_home.feature
│   ├── shutter_operations.feature
│   ├── telemetry_monitoring.feature
│   └── error_handling.feature
├── steps/                       # Step definitions
│   ├── common_steps.py          # Shared step definitions
│   ├── error_handling_steps.py  # Error handling steps
│   └── startup_shutdown_steps.py # Startup/shutdown steps
├── environment.py               # Behave configuration
├── run_tests.py                 # Test runner script
├── requirements.txt             # Test dependencies
└── README.md                    # This file
```

## 🔧 Configuration

The test suite uses the same configuration system as the main dome controller:

### Environment Variables
- `DOME_TEST_MODE`: Set to 'smoke' or 'hardware'
- `DOME_CONFIG_FILE`: Path to custom configuration file

### Configuration Options
Tests respect all dome configuration settings:
- `azimuth_tolerance`: Positioning accuracy tolerance
- `motor_speed`: Motor operation speed
- `safety_timeouts`: Safety timeout values
- `safe_azimuth`: Safe parking position

## 🐛 Troubleshooting

### Common Issues

#### "behave not found"
```bash
pip install behave
```

#### "Import dome could not be resolved"
Make sure you're running from the correct directory:
```bash
cd indi_dome_driver
python test/run_tests.py
```

#### Hardware tests fail
1. Check dome configuration
2. Verify hardware connections
3. Test individual components
4. Check safety systems

### Test Output Interpretation

#### Smoke Test Indicators
- 🔹 "SMOKE TEST:" prefix on actions
- ✅ Quick completion times
- 📊 Simulated sensor readings

#### Hardware Test Indicators
- ⚡ "HARDWARE:" prefix on actions
- ⏰ Real timing delays
- 🔧 Actual sensor readings

### Debugging Failed Tests
1. **Check Error Messages**: Look for specific failure reasons
2. **Review Logs**: Check for hardware communication issues
3. **Verify Setup**: Ensure proper dome configuration
4. **Isolate Issues**: Run individual features to narrow down problems

## 🤝 Contributing

### Adding New Tests
1. Create feature files using Gherkin syntax
2. Implement step definitions in appropriate step files
3. Test in both smoke and hardware modes
4. Update documentation

### Test Writing Guidelines
- Use descriptive scenario names
- Include both positive and negative test cases
- Test edge conditions and error scenarios
- Ensure tests work in both modes
- Add appropriate safety checks

### Example Feature Addition
```gherkin
Feature: New Dome Operation
  As an observatory operator
  I want to perform a new dome operation
  So that I can achieve a specific goal

  Scenario: Successful operation
    Given the dome is ready
    When I perform the new operation
    Then the operation should succeed
    And no errors should be reported
```

## 📊 Test Coverage

The test suite aims for comprehensive coverage of:
- ✅ **Normal Operations**: All standard dome functions
- ✅ **Error Conditions**: Hardware failures and edge cases
- ✅ **Safety Systems**: Emergency stops and safety interlocks
- ✅ **Boundary Conditions**: Limits and extreme values
- ✅ **Integration**: Full system operation flows

## 📞 Support

For issues with the test suite:
1. Check this README for common solutions
2. Review test output for specific error messages
3. Verify dome configuration and setup
4. Test individual components in isolation

Remember: **Safety First!** Always use smoke test mode for development and only use hardware mode when necessary for final validation with proper safety precautions.
