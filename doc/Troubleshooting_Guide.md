# Troubleshooting Guide

**INDI K8055 Dome Driver - Problem Diagnosis and Resolution**

This guide helps diagnose and fix common issues with your dome driver system.

---

## 🔍 Quick Diagnosis

### Problem Categories

| Symptom | Category | Quick Check |
|---------|----------|-------------|
| INDI won't connect | Connection | USB cable, power, INDI server running |
| Scripts fail with import errors | Python/Dependencies | PYTHONPATH, pyk8055 installation |
| Dome doesn't move | Hardware | K8055 connection, motor power, configuration |
| Inaccurate positioning | Calibration | Home position, ticks_to_degrees setting |
| Timeouts and errors | Configuration | Timeout settings, hardware response |

---

## 🔧 Connection Issues

### "Cannot Connect to Dome"

**Symptoms:**
- INDI client shows connection failed
- Scripts fail with connection errors
- No response from dome hardware

**Diagnosis Steps:**

1. **Check Hardware Connection:**
   ```bash
   # Verify K8055 USB detection
   lsusb | grep -i velleman
   ```
   **Expected:** Shows Velleman device
   **If missing:** Check USB cable, try different port

2. **Test Basic Connectivity:**
   ```bash
   cd /home/pi/indi_k8055_dome_driver
   make hardware-test-connect
   ```
   **Expected:** Shows successful connection
   **If fails:** Hardware or driver issue

3. **Check INDI Server:**
   ```bash
   # Check if INDI server is running
   ps aux | grep indiserver

   # Restart INDI server
   sudo killall indiserver
   indiserver -v indi_dome_script &
   ```

**Solutions:**
- **USB Issues:** Try different USB port, check cable quality
- **Power Issues:** Verify K8055 power LED, check power supply
- **Driver Issues:** Reinstall libk8055, check pyk8055 installation

### "Cannot Import pyk8055" Errors

**Symptoms:**
- Python import errors in scripts
- ModuleNotFoundError: No module named 'pyk8055'
- Scripts work in mock mode but fail in hardware mode

**Diagnosis Steps:**

1. **Test Python Import:**
   ```bash
   # Test from system Python
   python3 -c "import pyk8055; print('✅ pyk8055 available')"

   # Test from virtual environment
   source /home/pi/indi_k8055_dome_driver/venv/bin/activate
   python3 -c "import pyk8055; print('✅ pyk8055 available')"
   ```

2. **Check PYTHONPATH:**
   ```bash
   echo $PYTHONPATH
   python3 -c "import sys; print('\\n'.join(sys.path))"
   ```

**Solutions:**

**Option 1: System-wide Installation**
```bash
# Reinstall pyk8055 system-wide
cd /tmp/libk8055/src/pyk8055
sudo python3 setup.py install
```

**Option 2: Virtual Environment Path**
```bash
# Add pyk8055 to virtual environment
source /home/pi/indi_k8055_dome_driver/venv/bin/activate
echo "/path/to/pyk8055" > venv/lib/python3.*/site-packages/pyk8055.pth
```

**Option 3: Environment Variable**
```bash
# Add to ~/.bashrc
export PYTHONPATH="/tmp/libk8055/src/pyk8055:$PYTHONPATH"
source ~/.bashrc
```

---

## ⚙️ Hardware Issues

### "Dome Moves But Wrong Direction"

**Symptoms:**
- Clockwise command moves counter-clockwise
- Goto commands go to wrong position
- Home position incorrect

**Diagnosis:**
```bash
# Test individual movement commands
cd /home/pi/indi_k8055_dome_driver/indi_driver/scripts
python3 move_cw.py   # Observe actual direction
python3 abort.py
python3 move_ccw.py  # Observe actual direction
python3 abort.py
```

**Solutions:**
1. **Swap Motor Control Pins:**
   ```json
   {
     "pins": {
       "rotation_cw": 2,    // Was 1
       "rotation_ccw": 1    // Was 2
     }
   }
   ```

2. **Check Motor Wiring:**
   - Verify motor connections to relay board
   - Check relay board wiring to K8055 outputs
   - Ensure correct motor phases

### "Dome Doesn't Stop at Positions"

**Symptoms:**
- Goto commands overshoot target
- Home position varies each time
- Position drifts over time

**Diagnosis:**
```bash
# Run calibration test to measure accuracy
make test-calibrate

# Check specific position accuracy
python3 indi_driver/scripts/goto.py 90
python3 indi_driver/scripts/status.py
# Compare reported position to actual position
```

**Solutions:**
1. **Calibrate ticks_to_degrees:**
   ```json
   {
     "dome": {
       "ticks_to_degrees": 0.95  // Adjust based on calibration data
     }
   }
   ```

2. **Calibrate Home Position:**
   ```json
   {
     "dome": {
       "home_position": 15.5  // Adjust to actual home sensor position
     }
   }
   ```

3. **Check Mechanical Issues:**
   - Verify home switch operation
   - Check for mechanical slop or backlash
   - Ensure dome rotates smoothly

### "Shutter Won't Operate"

**Symptoms:**
- Open/close commands have no effect
- Shutter moves wrong direction
- Limit switches not detected

**Diagnosis:**
```bash
# Test shutter pins individually
python3 -c "
from indi_driver.lib.config import DomeConfig
from indi_driver.lib.dome import Dome
config = DomeConfig('indi_driver/dome_config.json')
dome = Dome(config)

# Test open pin
dome.k8055.SetDigitalChannel(config.pins.shutter_open)
print('Open pin activated - check shutter movement')
input('Press Enter to continue...')

# Test close pin
dome.k8055.ClearDigitalChannel(config.pins.shutter_open)
dome.k8055.SetDigitalChannel(config.pins.shutter_close)
print('Close pin activated - check shutter movement')
input('Press Enter to continue...')

dome.k8055.ClearDigitalChannel(config.pins.shutter_close)
"
```

**Solutions:**
1. **Check Pin Configuration:**
   ```json
   {
     "pins": {
       "shutter_open": 3,           // Verify correct pin
       "shutter_close": 4,          // Verify correct pin
       "shutter_open_sensor": 2,    // Check limit switch
       "shutter_close_sensor": 3    // Check limit switch
     }
   }
   ```

2. **Test Limit Switches:**
   ```bash
   # Read limit switch states
   python3 -c "
   from indi_driver.lib.config import DomeConfig
   from indi_driver.lib.dome import Dome
   config = DomeConfig('indi_driver/dome_config.json')
   dome = Dome(config)
   open_switch = dome.k8055.ReadDigitalChannel(config.pins.shutter_open_sensor)
   close_switch = dome.k8055.ReadDigitalChannel(config.pins.shutter_close_sensor)
   print(f'Open limit: {open_switch}, Close limit: {close_switch}')
   "
   ```

---

## ⏱️ Timeout and Performance Issues

### "Operations Timeout"

**Symptoms:**
- Commands fail with timeout errors
- Long delays before operations complete
- Intermittent operation failures

**Diagnosis:**
```bash
# Test with extended timeouts
export DOME_TEST_MODE=hardware
python3 test/integration/test_indi_scripts.py::TestINDIScripts::test_goto_script -v
```

**Solutions:**
1. **Increase Timeout Settings:**
   ```json
   {
     "dome": {
       "max_rotation_time": 600,    // Increase from 300
       "command_timeout": 30        // Increase from 10
     }
   }
   ```

2. **Check Motor Performance:**
   - Verify adequate motor power supply
   - Check for mechanical resistance
   - Ensure dome is properly balanced

3. **Optimize Communication:**
   - Use shorter, high-quality USB cables
   - Avoid USB hubs if possible
   - Check for USB interference

### "Slow Operation"

**Symptoms:**
- Dome rotates very slowly
- Commands take longer than expected
- Position updates are delayed

**Diagnosis:**
```bash
# Measure actual rotation speed
make test-calibrate
# Review timing results in output
```

**Solutions:**
1. **Check Power Supply:**
   - Verify motor voltage and current capacity
   - Check for voltage drops under load
   - Ensure adequate power supply sizing

2. **Mechanical Issues:**
   - Lubricate dome rotation mechanism
   - Check for binding or friction
   - Verify dome balance and alignment

---

## 🌧️ Weather and Safety Issues

### "Rain Detection Not Working"

**Symptoms:**
- Shutter operations proceed in rain
- Weather safety not triggering
- Rain override not respected

**Diagnosis:**
```bash
# Check weather detection
echo $WEATHER_RAINING
export WEATHER_RAINING=true

# Test rain blocking
python3 indi_driver/scripts/open.py
# Should fail with rain warning
```

**Solutions:**
1. **Set Weather Variables:**
   ```bash
   # In /etc/environment or ~/.bashrc
   export WEATHER_RAINING=true
   ```

2. **Integrate Weather Station:**
   - Connect weather station to set WEATHER_RAINING variable
   - Use rain sensor input to K8055 digital input
   - Script weather monitoring to update environment

### "Emergency Stop Not Working"

**Symptoms:**
- Abort command doesn't stop motion
- Hardware continues moving after abort
- Emergency procedures ineffective

**Diagnosis:**
```bash
# Test abort functionality
cd /home/pi/indi_k8055_dome_driver/indi_driver/scripts
python3 move_cw.py &
sleep 2
python3 abort.py
# Motion should stop within 1-2 seconds
```

**Solutions:**
1. **Check Abort Script:**
   - Verify abort.py script execution
   - Check relay response time
   - Test hardware emergency stop

2. **Hardware Emergency Stop:**
   - Install physical emergency stop button
   - Wire to cut motor power directly
   - Test monthly for reliable operation

---

## 🔄 Recovery Procedures

### Returning to Safe State

**If system becomes unstable:**

1. **Immediate Safety:**
   ```bash
   # Stop all motion
   cd /home/pi/indi_k8055_dome_driver/indi_driver/scripts
   python3 abort.py

   # Close shutter (if safe)
   python3 close.py

   # Move to home position
   python3 park.py
   ```

2. **Reset to Mock Mode:**
   ```bash
   # Switch to development config
   cd /home/pi/indi_k8055_dome_driver
   cp examples/dome_config_development.json indi_driver/dome_config.json

   # Test in mock mode
   python test/run_tests.py --mode smoke
   ```

3. **Hardware Reset:**
   ```bash
   # Disconnect USB, wait 5 seconds, reconnect
   # Restart INDI server
   sudo killall indiserver
   indiserver -v indi_dome_script &
   ```

### Configuration Recovery

**If configuration becomes corrupted:**

1. **Restore from Template:**
   ```bash
   # Backup current config
   cp indi_driver/dome_config.json dome_config_backup.json

   # Restore from template
   cp examples/dome_config_production.json indi_driver/dome_config.json
   ```

2. **Validate Configuration:**
   ```bash
   # Test configuration loading
   python3 -c "
   from indi_driver.lib.config import DomeConfig
   config = DomeConfig('indi_driver/dome_config.json')
   print('✅ Configuration valid')
   "
   ```

### System Recovery

**If system becomes completely unresponsive:**

1. **Restart Services:**
   ```bash
   sudo systemctl restart indi
   sudo reboot  # If needed
   ```

2. **Reinstall Driver:**
   ```bash
   # Fresh clone
   cd /home/pi
   mv indi_k8055_dome_driver indi_k8055_dome_driver.backup
   git clone https://github.com/YOUR-USERNAME/indi_k8055_dome_driver.git
   cd indi_k8055_dome_driver
   ./setup_venv.sh

   # Restore configuration
   cp ../indi_k8055_dome_driver.backup/indi_driver/dome_config.json indi_driver/
   ```

---

## 📞 Support Resources

### Diagnostic Information Collection

**When seeking help, collect this information:**

```bash
# System information
uname -a
lsusb | grep -i velleman
python3 --version

# Driver status
cd /home/pi/indi_k8055_dome_driver
git status
git log --oneline -5

# Configuration
cat indi_driver/dome_config.json

# Test results
python test/run_tests.py --mode smoke > diagnostic_output.txt 2>&1
```

### Log Files

**Key log locations:**
- INDI server logs: Check terminal where indiserver is running
- System USB logs: `dmesg | grep -i usb`
- Python error logs: Script output and error messages

### Community Resources

- **Documentation**: Check all user guides for detailed procedures
- **Testing**: Use comprehensive test suite to isolate issues
- **Configuration**: Reference example configurations for guidance

---

*This troubleshooting guide covers the most common issues. Always prioritize safety - when in doubt, stop all operations and seek assistance.*
