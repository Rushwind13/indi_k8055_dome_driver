# Contributing to INDI Dome Driver

Thank you for your interest in contributing to the INDI Dome Driver! This guide will help you get started with contributing to this astronomical observatory automation project.

## 🚨 Important Safety Notice

This software controls physical hardware that can cause injury or property damage. When contributing:

- **Always test in smoke mode first** before any hardware testing
- **Never submit code that bypasses safety checks**
- **Document any changes that affect safety behavior**
- **Consider the impact on real observatory operations**

## 🚀 Quick Start for Contributors

### 1. Fork and Clone
```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/indi_k8055_dome_driver.git
cd indi_k8055_dome_driver
```

### 2. Set Up Development Environment
```bash
# Automated setup (recommended)
make dev-setup
source venv/bin/activate

# Manual setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r test/requirements.txt
pre-commit install
```

### 3. Verify Setup
```bash
make ci  # Should pass all checks
```

## � Developer Reference Documents

This development directory contains detailed technical documentation for contributors:

### Task Planning and Implementation History
- **[PRODUCTION_READINESS_TASKS.md](PRODUCTION_READINESS_TASKS.md)** - Complete task tracking for production readiness implementation (Tasks 1-8)
- **[HARDWARE_INTEGRATION_TEST_PLAN.md](HARDWARE_INTEGRATION_TEST_PLAN.md)** - Comprehensive 8-hour hardware integration testing plan with rollback procedures

### User Documentation (Main Directory)
For end-user documentation, see the doc/ directory:
- **[Installation Guide](../doc/Installation_Guide.md)** - Raspberry Pi setup and installation
- **[User Guide](../doc/User_Guide.md)** - Day-to-day operations and configuration
- **[Troubleshooting Guide](../doc/Troubleshooting_Guide.md)** - Problem diagnosis and solutions
- **[Hardware Test Sequencing](../doc/Hardware_Test_Sequencing.md)** - Hardware testing procedures
- **[Environment Variables](../doc/Environment_Variables.md)** - Complete configuration variable reference

## �🔄 Development Workflow

### Branch Strategy
- `main`: Production-ready code (protected)
- `develop`: Integration branch for features
- `feature/description`: Feature development
- `hotfix/description`: Critical production fixes

### Making Changes

1. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-description
   ```

2. **Develop with Quality Checks**:
   ```bash
   # Make your changes
   # Pre-commit hooks run automatically
   git add .
   git commit -m "Clear description of changes"
   ```

3. **Test Locally**:
   ```bash
   make ci  # Runs all checks: format, lint, test, security
   ```

4. **Push and Create PR**:
   ```bash
   git push origin feature/your-feature-description
   # Create Pull Request on GitHub
   ```

## ✅ Pull Request Requirements

Your PR must meet these requirements to be merged:

### Automated Checks (Must Pass)
- ✅ **Code Formatting**: Black and isort
- ✅ **Linting**: flake8 and mypy
- ✅ **Security**: bandit scanning
- ✅ **Tests**: All unit and BDD smoke tests pass
- ✅ **CI**: All GitHub Actions workflows pass

### Manual Review Requirements
- ✅ **Code Review**: Approved by project maintainer
- ✅ **Documentation**: Updated for new features
- ✅ **Tests**: Added for new functionality
- ✅ **Safety**: No bypassing of safety mechanisms
- ✅ **Backward Compatibility**: Existing APIs preserved

## 🧪 Testing Standards

### Test Types
1. **Unit Tests** (`pytest`): Test individual components
2. **BDD Smoke Tests** (`behave`): Integration tests without hardware
3. **BDD Hardware Tests** (`behave`): Full integration with mock hardware

### Adding Tests
```bash
# Unit tests
pytest test/test_your_feature.py -v

# BDD tests
python test/run_tests.py --feature your_feature

# Run all tests
make test
```

### Test Requirements
- **New features**: Must include both unit and BDD tests
- **Bug fixes**: Must include regression tests
- **Safety features**: Require comprehensive test coverage
- **Hardware interactions**: Must work in both smoke and hardware modes

## 📝 Code Standards

### Formatting
- **Line length**: 88 characters (Black standard)
- **Import sorting**: isort with Black profile
- **Docstrings**: Google style for functions and classes

### Quality Checks
```bash
# Format code
make format

# Check formatting
make format-check

# Run linting
make lint

# Security scan
make security
```

### Python Standards
- **Type hints**: Required for new functions
- **Docstrings**: Required for public functions and classes
- **Error handling**: Explicit exception handling
- **Safety first**: Always consider hardware safety implications

## 📋 Commit Message Guidelines

Use clear, descriptive commit messages:

```bash
# Good
git commit -m "Add timeout protection for dome rotation"
git commit -m "Fix encoder counting bug in home detection"
git commit -m "Update README with new safety procedures"

# Less good
git commit -m "Fix bug"
git commit -m "Update code"
git commit -m "Changes"
```

## 🐛 Reporting Issues

### Bug Reports
Include in your issue:
- **Clear title** describing the problem
- **Steps to reproduce** with exact commands
- **Expected vs actual behavior**
- **Environment**: OS, Python version, hardware
- **Configuration**: Relevant dome_config.json sections
- **Test mode**: Smoke, hardware, or both
- **Error messages**: Full stack traces

### Feature Requests
Include in your issue:
- **Use case**: What problem this solves
- **Proposed solution**: How it should work
- **Alternatives**: Other approaches considered
- **Safety impact**: How this affects hardware safety
- **Breaking changes**: Impact on existing functionality

## 🔧 Development Commands

```bash
# Environment setup
make dev-setup          # Complete development environment setup
make venv               # Create virtual environment only
source venv/bin/activate # Activate environment

# Code quality
make format             # Auto-format with black and isort
make lint               # Run flake8, mypy, bandit
make ci                 # Run all CI checks locally

# Testing
make test               # Unit tests + BDD smoke tests
make test-smoke         # Fast BDD smoke tests only
make test-full          # Complete BDD test suite

# Utilities
make clean              # Clean build artifacts
make help               # Show all commands
```

## 🏗️ Project Structure

```
indi_k8055_dome_driver/
├── indi_driver/           # Core driver implementation
│   ├── scripts/           # 11 INDI driver scripts
│   └── lib/               # Core classes (dome.py, config.py, pyk8055_wrapper.py)
├── examples/              # Configuration templates
├── test/                  # Comprehensive test suite
├── development/           # Developer documentation and tools
├── doc/                   # Technical documentation
├── requirements*.txt      # Dependencies
├── setup_venv.sh         # Environment setup script
├── Makefile              # Development commands
└── .pre-commit-config.yaml # Pre-commit hooks
```

## 🔒 Security Considerations

### Code Security
- **Input validation**: Validate all external inputs
- **Dependency scanning**: Keep dependencies updated
- **Secret management**: No hardcoded credentials
- **Error messages**: Don't expose sensitive information

### Hardware Safety
- **Timeout protection**: All operations must have timeouts
- **Limit checking**: Verify all position and movement limits
- **Emergency stops**: Preserve emergency stop functionality
- **Configuration validation**: Validate all configuration inputs

## 📚 Additional Resources

- **[Installation Guide](../doc/Installation_Guide.md)**: Complete setup instructions
- **[User Guide](../doc/User_Guide.md)**: Day-to-day operations
- **[Troubleshooting Guide](../doc/Troubleshooting_Guide.md)**: Problem diagnosis
- **[Hardware Test Sequencing](../doc/Hardware_Test_Sequencing.md)**: Hardware testing procedures
- **[Environment Variables](../doc/Environment_Variables.md)**: Configuration variable reference
- **[Test Documentation](../test/README.md)**: Testing framework details
- **[Architecture Documentation](../doc/Architecture.md)**: System design

## 💬 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For general questions and ideas
- **Code Review**: For getting feedback on your contributions

## 📄 License

By contributing, you agree that your contributions will be licensed under the GNU General Public License v3.0.

---

**Remember**: Observatory automation affects real equipment and safety. Always prioritize safety and test thoroughly!
