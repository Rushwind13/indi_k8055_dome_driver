# INDI K8055 Dome Driver

**Complete INDI dome driver for Velleman K8055-based observatory dome controllers.**

## 🎯 Quick Start

This is the INDI dome driver. Configure your INDI dome_script driver with:

```
Script Folder: /path/to/indi_k8055_dome_driver/scripts
Connect script: connect.py
Disconnect script: disconnect.py
Get status script: status.py
Open shutter script: open.py
Close shutter script: close.py
Park script: park.py
Unpark script: unpark.py
Goto script: goto.py
Move clockwise script: move_cw.py
Move counter clockwise script: move_ccw.py
Abort motion script: abort.py
```

## 📁 Project Structure

```
scripts/          # The 11 INDI driver scripts (THE DRIVER)
dome.py           # Core dome control class
pyk8055_wrapper.py # K8055 hardware interface
config.py         # Configuration management
test/             # Comprehensive test suite
```

## 🔧 Setup

1. **Install dependencies**:
   ```bash
   ./setup_venv.sh
   pip install -r requirements.txt
   ```

2. **Test the driver**:
   ```bash
   python test/test_indi_scripts.py
   ```

3. **Configure INDI**: Point your dome_script driver to the `scripts/` directory

## 🏗️ Architecture

```
INDI dome_script ← scripts/ ← dome.py ← pyk8055_wrapper.py ← K8055 Hardware
```

The driver uses a mock K8055 interface for development and testing, with easy production hardware swapping.

## 📋 Requirements

- Python 3.8+
- INDI dome_script driver
- Velleman K8055 USB interface (or mock for testing)

## 🧪 Testing

```bash
# Test all components
python test/run_tests.py

# Test INDI driver specifically
python test/test_indi_scripts.py

# Test hardware wrapper
python test/test_wrapper_integration.py
```

## 📚 Documentation

- `scripts/README.md` - INDI script details
- `doc/Architecture.md` - System design rules
- `test/README.md` - Testing guide

## 🚀 Production Deployment

1. Install on Raspberry Pi or control computer
2. Configure dome_config.json for your hardware
3. Point INDI dome_script to scripts/ directory
4. Verify with test suite

**This driver is production-ready and INDI-compliant.**
