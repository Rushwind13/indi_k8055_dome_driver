# INDI K8055 Dome Driver

**Production-ready INDI dome driver for Velleman K8055-based observatory dome controllers with Python 2.7 support.**

## 🚀 For Users

**New to this driver?** Start here:
- **[Installation Guide](doc/Installation_Guide.md)** - Complete setup on Raspberry Pi
- **[User Guide](doc/User_Guide.md)** - Day-to-day operation and configuration
- **[Python 2.7 Validation Guide](doc/py27_validation/Python27_Validation_Guide.md)** - Legacy Python support
- **[Troubleshooting Guide](doc/Troubleshooting_Guide.md)** - Problem diagnosis and solutions

## 🎯 Quick Start

**Already installed?** Configure your INDI dome_script driver:

```
Script Folder: /path/to/indi_k8055_dome_driver/indi_driver/scripts
Connect script: connect.py
Disconnect script: disconnect.py
Get status script: status.py
Park script: park.py
Unpark script: unpark.py
Goto script: goto.py
Move clockwise script: move_cw.py
Move counter clockwise script: move_ccw.py
Open shutter script: open.py
Close shutter script: close.py
Abort motion script: abort.py
```

**Python 2.7 Users:** Use `/indi_driver/python2/scripts/` instead.

## 🐍 Python 2.7 Support

Complete Python 2.7 compatibility with state persistence:

```bash
# Validate Python 2.7 installation
make test-py27

# Complete validation with linting
make test-py27-full

# Deploy to Python 2.7 system
cp -r indi_driver/python2/ /target/path/
```

**Key Features:**
- ✅ Full dome control functionality
- ✅ State persistence between script executions
- ✅ All sensor states preserved (position, encoders, home, shutter)
- ✅ Python 2.7 compatible syntax (no f-strings, modern features)
- ✅ Comprehensive test suite

## 🏗️ Architecture

```
INDI dome_script ← indi_driver/scripts/ ← lib/dome.py ← lib/pyk8055_wrapper.py ← K8055 Hardware
                 ← indi_driver/python2/scripts/ (Python 2.7 compatible)
```

The driver automatically switches between mock mode (development) and hardware mode (production) based on configuration. Python 2.7 version includes comprehensive state persistence system.

## 🧪 Testing

```bash
# Quick development test (Python 3)
python test/run_tests.py --mode smoke

# Python 2.7 validation
make test-py27

# Hardware validation (after installation)
export DOME_TEST_MODE=hardware
make test-hardware-safe
```

## 📁 Project Structure

```
indi_driver/          # Core driver implementation
  scripts/            # 11 INDI driver scripts (THE DRIVER)
  lib/                # Core dome control classes
    dome.py           # Main dome control logic
    pyk8055_wrapper.py # K8055 hardware abstraction
    config.py         # Configuration management
examples/             # Configuration templates
test/                 # Comprehensive test suite
```

## 📚 Complete Documentation

**User Documentation:**
- **[Installation Guide](doc/Installation_Guide.md)** - Raspberry Pi setup, K8055 installation, PYTHONPATH configuration
- **[User Guide](doc/User_Guide.md)** - Daily operations, configuration, monitoring, maintenance
- **[Troubleshooting Guide](doc/Troubleshooting_Guide.md)** - Problem diagnosis, error recovery, support
- **[Environment Variables](doc/Environment_Variables.md)** - Complete reference for all configuration variables

**Developer Documentation:**
- **[Hardware Test Sequencing](doc/Hardware_Test_Sequencing.md)** - Hardware testing procedures
- **[Architecture](doc/Architecture.md)** - System design and requirements
- **[Testing Guide](test/README.md)** - Development and validation testing

**Production-Ready Features:**
- ✅ Complete mock/hardware abstraction
- ✅ Comprehensive test suite (Unit, Integration, BDD)
- ✅ Hardware safety systems and emergency controls
- ✅ Weather-aware operations (rain detection)
- ✅ Calibration and position accuracy validation
- ✅ INDI-compliant script interface
- ✅ Production deployment procedures

**This driver is enterprise-ready for observatory automation.**
