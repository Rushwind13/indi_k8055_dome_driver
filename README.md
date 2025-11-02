# INDI Dome Driver

🔭 **A comprehensive Python-based dome control driver for astronomical observatories using the Velleman K8055 USB interface board.**


**⚠️ Important Safety Notice**: This software controls physical hardware that can cause injury or property damage. Always follow proper safety procedures, test thoroughly in safe conditions, and never operate unattended. The authors assume no liability for damage or injury resulting from use of this software.


[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![BDD Tests](https://img.shields.io/badge/tests-BDD%20%2B%20Cucumber-green.svg)](test/)

## 🌟 Features

### Core Functionality
- **Dome Rotation Control**: Precise clockwise and counter-clockwise rotation
- **Home Position Detection**: Automatic finding and returning to home position
- **Encoder-based Positioning**: Accurate azimuth tracking with optical encoders
- **Shutter Control**: Safe opening/closing with limit switch monitoring
- **Safety Interlocks**: Multiple safety systems to prevent hardware damage

### Advanced Features
- **Configuration-Driven**: JSON-based configuration system for easy customization
- **Dual Test Modes**: Safe smoke testing and real hardware validation
- **Comprehensive Logging**: Detailed operation logging for debugging and monitoring
- **Error Recovery**: Automatic error detection and recovery procedures
- **BDD Test Suite**: Complete Cucumber-based test coverage

### Safety Features
- **Emergency Stop**: Immediate halt of all operations
- **Timeout Protection**: Automatic shutdown on communication failures
- **Limit Switch Monitoring**: Hardware safety limits for shutter operations
- **Stall Detection**: Motor stall detection and protection
- **Configuration Validation**: Input validation and safe defaults

## 🛠️ Development Workflow

This project follows professional development practices with automated testing, code quality checks, and continuous integration.

### Development Environment Setup

#### Quick Start (Recommended)
```bash
# Clone the repository
git clone https://github.com/Rushwind13/indi_dome_driver.git
cd indi_dome_driver

# Set up complete development environment
make dev-setup

# Activate virtual environment
source venv/bin/activate
```

#### Manual Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r test/requirements.txt

# Install pre-commit hooks
pre-commit install
```

### Development Commands

```bash
# Run all tests (unit + BDD smoke tests)
make test

# Run only fast smoke tests
make test-smoke

# Check code formatting and linting
make lint

# Format code automatically
make format

# Run security checks
make security

# Run all CI checks locally
make ci

# Clean up build artifacts
make clean
```

### Branching Strategy

- **`main`**: Production-ready code, protected branch
- **`develop`**: Integration branch for features
- **`feature/*`**: Feature development branches
- **`hotfix/*`**: Critical fixes for production

### Contribution Workflow

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Develop with Quality Checks**:
   ```bash
   # Make your changes
   # Pre-commit hooks automatically run on commit
   git add .
   git commit -m "Add your feature"
   ```

3. **Run Local CI Checks**:
   ```bash
   make ci  # Runs formatting, linting, and tests
   ```

4. **Push and Create Pull Request**:
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

5. **PR Requirements**:
   - ✅ All CI checks must pass
   - ✅ Code coverage maintained
   - ✅ Code review approved
   - ✅ Branch up to date with main

### Code Quality Standards

#### Automated Checks (Pre-commit)
- **Black**: Code formatting (88 character line length)
- **isort**: Import sorting and organization
- **flake8**: Code linting and style checking
- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning
- **pytest**: Unit test execution
- **behave**: BDD smoke test execution

#### Manual Review Requirements
- Code follows Python PEP 8 style guidelines
- Functions and classes have proper docstrings
- Complex logic includes inline comments
- Changes include appropriate tests
- Breaking changes are documented

### Testing Strategy

#### Test Types
1. **Unit Tests** (`pytest`): Fast, isolated component testing
2. **BDD Smoke Tests** (`behave`): Safe integration testing without hardware
3. **BDD Hardware Tests** (`behave`): Full integration testing with mock hardware
4. **Security Tests** (`bandit`, `safety`): Vulnerability scanning

#### Running Tests
```bash
# Quick smoke tests (< 30 seconds)
make test-smoke

# Full test suite (includes unit tests)
make test

# Run specific test files
pytest test/test_config.py
python test/run_tests.py --feature rotation

# Run with coverage
pytest --cov=. --cov-report=html
```

### Continuous Integration

GitHub Actions automatically runs on every push and PR:

- **Code Quality**: Formatting, linting, type checking
- **Security**: Vulnerability scanning, dependency checking
- **Testing**: Multi-version Python testing (3.7-3.11)
- **Documentation**: Builds and validates documentation

**Pull Request Merge Requirements**:
- ✅ All CI checks pass
- ✅ Code review approved
- ✅ Branch is up to date
- ✅ No merge conflicts

## 🔧 Hardware Requirements

### Primary Components
- **Velleman K8055 USB Interface Board**
- **K8055D.dll** (Windows) or appropriate Linux drivers
- **USB cable** connecting K8055 to control computer

### Dome Hardware
- **Rotation Motor**: Bidirectional motor with direction control
- **Home Position Switch**: Sensor to detect dome home position
- **Optical Encoders**: Position feedback sensors (2-channel quadrature)
- **Shutter Motor**: Motor for dome shutter operation
- **Limit Switches**: Upper and lower shutter position sensors

### Electrical Connections
The K8055 board provides:
- **8 Digital Inputs**: For switches, encoders, and position sensors
- **8 Digital Outputs**: For motor control and status indicators
- **2 Analog Inputs**: For analog sensors and monitoring
- **2 Analog Outputs**: For variable speed control (optional)

## 🚀 Quick Start

### For Users (Production Use)

1. **Clone and set up the environment:**
   ```bash
   git clone https://github.com/Rushwind13/indi_dome_driver.git
   cd indi_dome_driver

   # Set up virtual environment and dependencies
   ./setup_venv.sh
   source venv/bin/activate
   ```

2. **Configure for your hardware:**
   ```bash
   cp dome_config.json.example dome_config.json
   # Edit dome_config.json to match your hardware setup
   ```

3. **Validate setup:**
   ```bash
   python test/validate_setup.py
   make test-smoke  # Run quick safety checks
   ```

### For Developers

1. **Set up development environment:**
   ```bash
   git clone https://github.com/Rushwind13/indi_dome_driver.git
   cd indi_dome_driver

   # Complete development setup with all tools
   make dev-setup
   source venv/bin/activate
   ```

2. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Verify development environment:**
   ```bash
   make ci  # Run all quality checks
   ```

### Basic Usage

```python
from dome import Dome
from config import load_config

# Initialize dome with configuration
config = load_config()
dome = Dome(config)

# Find home position
dome.find_home()

# Rotate to specific azimuth
dome.slew_to_azimuth(180)  # Point south

# Rotate by specific amount
dome.rotate_clockwise(90)   # 90 degrees clockwise
dome.rotate_counter_clockwise(45)  # 45 degrees counter-clockwise

# Shutter operations
dome.open_shutter()
dome.close_shutter()

# Check status
if dome.isHome():
    print("Dome is at home position")
if not dome.isClosed():
    print("Shutter is open")
```

## 📋 Configuration

The driver uses a comprehensive JSON configuration system in `dome_config.json`:

### Pin Assignments
```json
{
  "pins": {
    "encoder_a": 1,
    "encoder_b": 2,
    "home_switch": 3,
    "shutter_upper_limit": 1,
    "shutter_lower_limit": 2,
    "dome_rotate": 1,
    "dome_direction": 2,
    "shutter_motor": 3
  }
}
```

### Calibration Settings
```json
{
  "calibration": {
    "home_position": 0,
    "ticks_to_degrees": 0.1,
    "azimuth_tolerance": 2,
    "motor_speed": 50,
    "safe_azimuth": 0
  }
}
```

### Safety Timeouts
```json
{
  "timeouts": {
    "rotation_timeout": 300,
    "shutter_timeout": 60,
    "home_timeout": 180,
    "communication_timeout": 5
  }
}
```

### Test Configuration
```json
{
  "smoke_test": true,
  "debug_mode": false,
  "log_level": "INFO"
}
```

## 🧪 Testing

The project includes a comprehensive BDD (Behavior-Driven Development) test suite using Cucumber:

### Test Modes

#### 🔹 Smoke Test Mode (Default)
- **Safe**: No real hardware operations
- **Fast**: Quick execution with simulated responses
- **Development**: Perfect for development and CI/CD
```bash
python3 test/run_tests.py
```

#### ⚡ Hardware Test Mode
- **Real Operations**: Actual dome and shutter movements
- **Integration**: Complete end-to-end testing
- **⚠️ CAUTION**: Requires proper dome setup
```bash
python3 test/run_tests.py --mode hardware
```

### Test Features
The test suite covers:
- **Startup/Shutdown**: System initialization and safe shutdown
- **Dome Rotation**: All rotation operations and positioning
- **Home Operations**: Finding and returning to home position
- **Shutter Control**: Opening/closing with safety verification
- **Telemetry**: Position reporting and status monitoring
- **Error Handling**: Edge cases, failures, and recovery

### Running Tests

```bash
# Run all smoke tests (safe)
python3 test/run_tests.py

# Run specific feature
python3 test/run_tests.py --feature rotation

# List available test features
python3 test/run_tests.py --list-features

# Install test dependencies
pip install -r test/requirements.txt

# Validate test setup
python3 test/validate_setup.py
```

## 🛡️ Safety Considerations

### Hardware Safety
- **⚠️ Physical Safety**: Ensure dome area is clear before hardware tests
- **⚠️ Equipment Safety**: Verify dome is mechanically sound
- **⚠️ Emergency Procedures**: Have emergency stop procedures ready
- **⚠️ Supervision**: Never run hardware tests unattended

### Software Safety
- **Configuration Validation**: All inputs are validated
- **Safe Defaults**: System uses safe values when configuration is missing
- **Timeout Protection**: Operations timeout to prevent runaway conditions
- **Error Recovery**: Automatic error detection and safe shutdown

### Testing Safety
1. **Always start with smoke tests** to verify logic
2. **Use hardware mode only when necessary**
3. **Monitor hardware tests continuously**
4. **Have emergency stop readily available**

## 📁 Project Structure

```
indi_dome_driver/
├── dome.py                     # Main dome control class
├── config.py                   # Configuration management
├── pyk8055_wrapper.py          # K8055 hardware interface
├── pyk8055.py                  # K8055 driver
├── requirements.txt            # Python dependencies
├── dome_config.json.example    # Example configuration
├── smoke_test_config.json      # Smoke test configuration
├── test_dome.py               # Basic dome tests
├── test_shutter.py            # Basic shutter tests
├── test/                      # BDD test suite
│   ├── features/              # Cucumber feature files
│   ├── steps/                 # Step definitions
│   ├── run_tests.py          # Test runner
│   ├── validate_setup.py     # Setup validation
│   └── README.md             # Test documentation
└── README.md                  # This file
```

## 🔌 Hardware Setup

### K8055 Board Connections

#### Digital Inputs
- **I1**: Encoder Channel A
- **I2**: Encoder Channel B
- **I3**: Home Position Switch
- **I4**: Emergency Stop (optional)
- **I5**: Shutter Fully Open Switch
- **I6**: Shutter Fully Closed Switch

#### Digital Outputs
- **O1**: Dome Rotation Motor Enable
- **O2**: Dome Rotation Direction
- **O3**: Shutter Motor Control
- **O4**: Status LED (optional)

#### Analog Inputs
- **A1**: Shutter Upper Limit
- **A2**: Shutter Lower Limit

### Wiring Guidelines
1. **Use proper isolation** for motor control circuits
2. **Add debouncing** for mechanical switches
3. **Include fuses** in motor circuits for protection
4. **Ground all equipment** properly
5. **Use shielded cables** for encoder signals

## 🤝 Contributing

We welcome contributions to improve the dome driver! This project follows professional development practices to ensure code quality and reliability.

### Quick Contribution Guide

1. **Fork and Clone**:
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/indi_dome_driver.git
   cd indi_dome_driver
   ```

2. **Set Up Development Environment**:
   ```bash
   make dev-setup  # Sets up venv, installs deps, configures pre-commit
   source venv/bin/activate
   ```

3. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Develop with Quality Checks**:
   ```bash
   # Make your changes
   # Pre-commit hooks run automatically on commit
   make ci  # Run all checks locally before pushing
   ```

5. **Submit Pull Request**:
   - Push your branch to your fork
   - Create PR on GitHub targeting `main` branch
   - Ensure all CI checks pass

### Development Standards

#### Code Quality Requirements
- **Formatting**: Code must pass `black` and `isort` formatting
- **Linting**: Code must pass `flake8` and `mypy` checks
- **Security**: Code must pass `bandit` security scanning
- **Testing**: All tests must pass, maintain coverage
- **Documentation**: New features require documentation updates

#### Pull Request Requirements
- ✅ All GitHub Actions CI checks pass
- ✅ Code review approved by maintainer
- ✅ Branch is up to date with main
- ✅ No merge conflicts
- ✅ Tests added for new functionality
- ✅ Documentation updated if needed

### Adding Features

#### Before You Start
- Check existing issues and PRs to avoid duplication
- Open an issue to discuss major changes
- Ensure feature aligns with project goals

#### Development Process
1. **Follow Code Style**: Project uses Black formatting with 88-character lines
2. **Add Tests**: Both unit tests (`pytest`) and BDD scenarios (`behave`)
3. **Update Documentation**: README, docstrings, and comments
4. **Maintain Backward Compatibility**: Don't break existing APIs
5. **Consider Safety**: This controls physical hardware

#### Test Requirements
```bash
# Add unit tests in test/ directory
pytest test/test_your_feature.py

# Add BDD scenarios in test/features/
python test/run_tests.py --feature your_feature

# Ensure all tests pass
make test
```

### Reporting Issues

#### Bug Reports
Use the GitHub issue tracker with:
- **Clear title** describing the problem
- **Reproduction steps** with exact commands/code
- **Expected vs actual behavior**
- **Environment details**: OS, Python version, hardware setup
- **Configuration**: Relevant parts of dome_config.json
- **Test mode**: Whether issue occurs in smoke, hardware, or both modes

#### Feature Requests
- **Use case description**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives considered**: Other approaches evaluated
- **Breaking changes**: Impact on existing functionality

### Development Commands Reference

```bash
# Setup and environment
make dev-setup          # Complete development setup
make install-dev        # Install all dependencies
source venv/bin/activate # Activate virtual environment

# Code quality
make format             # Auto-format code (black + isort)
make lint               # Run all linting checks
make security           # Run security scans
make ci                 # Run all CI checks locally

# Testing
make test               # Run all tests (unit + BDD smoke)
make test-smoke         # Run only fast BDD smoke tests
make test-full          # Run complete BDD test suite

# Maintenance
make clean              # Clean build artifacts
make help               # Show all available commands
```

### Code Review Process

#### For Contributors
- Ensure CI passes before requesting review
- Respond to review feedback promptly
- Keep PRs focused and reasonably sized
- Update PR description if scope changes

#### For Maintainers
- Review for code quality, testing, and documentation
- Test functionality in both smoke and hardware modes
- Ensure changes align with project goals
- Provide constructive feedback

## 📚 Documentation

### API Documentation
- **Dome Class**: Main control interface
- **Configuration**: Complete configuration reference
- **Hardware Interface**: K8055 communication details
- **Safety Systems**: Error handling and recovery

### Additional Resources
- **[Test Suite Documentation](test/README.md)**: Complete testing guide
- **[Configuration Examples](dome_config.json.example)**: Hardware setup examples
- **[Safety Guidelines](#-safety-considerations)**: Important safety information

## 🐛 Troubleshooting

### Common Issues

#### K8055 Not Detected
```bash
# Check USB connection
lsusb | grep "10cf:5500"

# Verify permissions (Linux)
sudo chmod 666 /dev/bus/usb/*/device
```

#### Configuration Errors
```bash
# Validate configuration
python3 -c "from config import load_config; print(load_config())"

# Reset to defaults
cp dome_config.json.example dome_config.json
```

#### Test Failures
```bash
# Run setup validation
python3 test/validate_setup.py

# Check individual components
python3 test/run_tests.py --feature startup
```

### Getting Help
1. Check the [troubleshooting section](#-troubleshooting)
2. Review test output for specific errors
3. Verify hardware connections
4. Check configuration settings
5. Submit an issue with detailed information

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Observatory Automation Community**: For inspiration and best practices
- **INDI Project**: For standardized astronomical device interfaces
- **Velleman**: For the K8055 USB interface board
- **Python Testing Community**: For excellent BDD testing frameworks

## 📞 Support

For support and questions:
- **Issues**: Use the GitHub issue tracker
- **Discussions**: Use GitHub Discussions for general questions
- **Safety Concerns**: Always prioritize safety - stop operations if anything seems wrong

---
