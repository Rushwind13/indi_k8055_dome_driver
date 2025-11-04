# User Installation Guide

**INDI K8055 Dome Driver - Complete Installation and Setup**

This guide walks you through installing and configuring the INDI K8055 Dome Driver on your Raspberry Pi observatory computer.

---

## 📋 Prerequisites

### Hardware Requirements
- **Raspberry Pi** (3B+ or newer recommended)
- **Velleman K8055 USB Interface Board**
- **USB cable** for K8055 connection
- **Dome hardware** (motors, sensors, shutter)
- **Network connectivity** for remote access

### Software Requirements
- **Raspberry Pi OS** (Bullseye or newer)
- **INDI server** for telescope control integration
- **Python 3.8+** (included in recent Pi OS)

---

## 🚀 Installation

### Step 1: System Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install development tools and dependencies
sudo apt install -y python3 python3-pip python3-venv git build-essential
sudo apt install -y libusb-dev swig python3-dev
```

### Step 2: Install K8055 Library

```bash
# Install libk8055 system library
sudo apt install -y libk8055-dev

# If package not available, build from source:
git clone https://github.com/medved/libk8055.git /tmp/libk8055
cd /tmp/libk8055/src
make
sudo make install

# Build Python bindings
cd /tmp/libk8055/src/pyk8055
python3 setup.py build_ext --inplace
sudo python3 setup.py install
```

### Step 3: Download Dome Driver

```bash
# Clone the driver repository
cd /home/pi
git clone https://github.com/YOUR-USERNAME/indi_k8055_dome_driver.git
cd indi_k8055_dome_driver

# Set up Python virtual environment
./setup_venv.sh
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 4: Configure PYTHONPATH

**IMPORTANT**: The driver needs access to the `pyk8055` module.

#### Option A: System-wide Installation (Recommended)
If you installed pyk8055 system-wide (Step 2), the driver should work automatically.

#### Option B: Manual PYTHONPATH Configuration
If you have a custom pyk8055 installation:

```bash
# Add to your ~/.bashrc or /etc/environment
export PYTHONPATH="/path/to/your/pyk8055:$PYTHONPATH"

# Example if built in /tmp/libk8055:
export PYTHONPATH="/tmp/libk8055/src/pyk8055:$PYTHONPATH"
```

#### Option C: Virtual Environment Setup
```bash
# Activate your dome driver virtual environment
source /home/pi/indi_k8055_dome_driver/venv/bin/activate

# Add pyk8055 path to the virtual environment
echo "/path/to/your/pyk8055" > venv/lib/python3.*/site-packages/pyk8055.pth
```

### Step 5: Verify Installation

```bash
# Test K8055 library availability
cd /home/pi/indi_k8055_dome_driver
make check-k8055

# Verify Python can import pyk8055
python3 -c "import pyk8055; print('✅ pyk8055 module available')"

# Test driver in mock mode
source venv/bin/activate
python test/run_tests.py --mode smoke
```

---

## ⚙️ Configuration

### Create Production Configuration

```bash
cd /home/pi/indi_k8055_dome_driver

# Copy production template
cp examples/dome_config_production.json indi_driver/dome_config.json

# Edit configuration for your dome
nano indi_driver/dome_config.json
```

### Key Configuration Settings

```json
{
  "hardware": {
    "mock_mode": false,          // Set to false for real hardware
    "k8055_board_address": 0,    // Usually 0 unless multiple boards
    "debug": true                // Enable for initial setup
  },
  "dome": {
    "home_position": 0.0,        // Calibrate this value
    "ticks_to_degrees": 1.0,     // Calibrate this value
    "max_rotation_time": 300     // Maximum time for full rotation
  },
  "pins": {
    "rotation_cw": 1,            // Digital output pin for CW rotation
    "rotation_ccw": 2,           // Digital output pin for CCW rotation
    "shutter_open": 3,           // Digital output pin for shutter open
    "shutter_close": 4,          // Digital output pin for shutter close
    "home_switch": 1,            // Digital input pin for home sensor
    "shutter_open_sensor": 2,    // Digital input pin for shutter open limit
    "shutter_close_sensor": 3    // Digital input pin for shutter close limit
  }
}
```

### Pin Assignment Reference

**Digital Outputs (1-8):**
- Connect dome motor control relays
- Connect shutter motor control relays

**Digital Inputs (1-5):**
- Connect limit switches and sensors
- Use pull-up resistors for reliable operation

**Analog Inputs (1-2):**
- Available for position encoders (future enhancement)

---

## 🔌 Hardware Connection

### K8055 to Dome Wiring

```
K8055 Digital Outputs → Relay Board → Dome Motors
K8055 Digital Inputs ← Limit Switches ← Dome Sensors
K8055 USB Port → Raspberry Pi USB Port
```

### Safety Considerations

1. **Emergency Stop**: Ensure physical emergency stop is always accessible
2. **Power Isolation**: Use relay board to isolate motor power from control signals
3. **Limit Switches**: Wire limit switches as normally closed for safety
4. **Grounding**: Ensure proper grounding of all metal components

---

## 🧪 Initial Testing

### Step 1: Hardware Detection

```bash
cd /home/pi/indi_k8055_dome_driver

# Check USB connection
lsusb | grep -i velleman

# Test hardware connection (no movement)
make hardware-test-connect
```

### Step 2: Basic Function Test

```bash
# Test sensors without motors connected
export DOME_TEST_MODE=hardware
make test-hardware-safe
```

**Expected Output:**
- ✅ K8055 connection successful
- ✅ Configuration loaded correctly
- ✅ Digital I/O responding
- ✅ Abort system functional

### Step 3: Motor Testing (CAUTION)

**⚠️ SAFETY FIRST:**
- Ensure dome area is clear
- Have emergency stop ready
- Start with short movements only

```bash
# Test minimal dome movement (2-5 second rotations)
export DOME_TEST_MODE=hardware
make test-hardware-startup
```

---

## 🔧 INDI Integration

### Install INDI Server

```bash
# Install INDI if not already present
sudo apt install -y indi-bin

# Test INDI installation
indiserver --help
```

### Configure INDI Dome Driver

1. **Start INDI Server:**
   ```bash
   indiserver -v indi_dome_script &
   ```

2. **Connect from INDI Client** (KStars/Ekos):
   - **Server**: Your Raspberry Pi IP address
   - **Port**: 7624 (default)
   - **Driver**: Dome Script

3. **Configure Script Paths:**
   ```
   Script Folder: /home/pi/indi_k8055_dome_driver/indi_driver/scripts
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

---

## 🎯 Calibration

Once basic operations work, calibrate your dome:

### Step 1: Home Position Calibration

```bash
# Run home position repeatability test
make test-calibrate
```

Review the calibration results and update `home_position` in your configuration.

### Step 2: Position Accuracy Calibration

The calibration test will measure positioning accuracy and suggest adjustments to `ticks_to_degrees`.

### Step 3: Timing Calibration

Test results include rotation timing data to optimize `max_rotation_time` setting.

---

## ✅ Verification Checklist

- [ ] K8055 detected by USB system (`lsusb` shows Velleman device)
- [ ] pyk8055 Python module imports successfully
- [ ] Driver connects to hardware without errors
- [ ] Basic movement tests complete successfully
- [ ] INDI server recognizes dome_script driver
- [ ] INDI client can connect and control dome
- [ ] Home position is reliable and repeatable
- [ ] Position accuracy within acceptable tolerance (±2°)
- [ ] Emergency abort functions correctly
- [ ] All safety systems operational

---

## 🔗 Next Steps

After successful installation:

1. **Read the User Guide** ([User_Guide.md](User_Guide.md)) for day-to-day operation instructions
2. **Review the Troubleshooting Guide** ([Troubleshooting_Guide.md](Troubleshooting_Guide.md)) for common issues and solutions
3. **Check Environment Variables** ([Environment_Variables.md](Environment_Variables.md)) for configuration options
4. **Perform regular testing** using the hardware test sequences
5. **Monitor logs** for hardware health and performance

---

## 📞 Support

If you encounter issues:

1. **Check the Troubleshooting Guide** ([Troubleshooting_Guide.md](Troubleshooting_Guide.md)) for common solutions
2. **Verify PYTHONPATH** includes pyk8055 module location
3. **Test in mock mode** to isolate hardware vs software issues
4. **Review hardware connections** and power supplies
5. **Check system logs** for USB and hardware errors

---

*This installation guide provides everything needed to get your INDI K8055 Dome Driver operational. Take time with calibration - it's essential for reliable operation.*
