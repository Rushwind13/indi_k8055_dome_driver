# User Guide

**INDI K8055 Dome Driver - Day-to-Day Operation**

This guide covers regular use of your dome driver after installation and initial setup.

---

## 🚀 Quick Start

### Starting Your Dome System

1. **Power On Hardware:**
   - Turn on dome motors and control systems
   - Verify K8055 USB connection to Raspberry Pi

2. **Start INDI Server:**
   ```bash
   # SSH to your Raspberry Pi
   ssh pi@your-dome-controller-ip

   # Start INDI dome server
   indiserver -v indi_dome_script
   ```

3. **Connect from INDI Client:**
   - Open KStars/Ekos or your INDI client
   - Connect to dome server at your Pi's IP address
   - Test connection and basic operations

---

## 🎛️ Basic Operations

### Using INDI Client (KStars/Ekos)

**Connect to Dome:**
1. In your INDI client, connect to the dome
2. Wait for "Connected" status
3. Check that current position is displayed

**Home the Dome:**
1. Click "Park" to move dome to home position
2. Wait for "Parked" status
3. Dome should be at calibrated home position

**Rotate to Position:**
1. Click "Unpark" if dome is parked
2. Enter desired azimuth (0-360 degrees)
3. Click "Goto" or press Enter
4. Wait for dome to reach position

**Open/Close Shutter:**
1. Click "Open Shutter" to open
2. Click "Close Shutter" to close
3. Monitor shutter status indicator

**Emergency Stop:**
1. Click "Abort" to immediately stop all motion
2. Use physical emergency stop if needed

### Using Command Line Scripts

All operations can be performed directly via scripts:

```bash
cd /home/pi/indi_k8055_dome_driver/indi_driver/scripts

# Connect to dome
python3 connect.py

# Check status
python3 status.py
# Output format: "parked_status shutter_status azimuth_degrees"
# Example: "false true 180.5"

# Home the dome
python3 park.py

# Move to specific position
python3 unpark.py
python3 goto.py 90  # Rotate to 90 degrees

# Rotate manually
python3 move_cw.py    # Start clockwise rotation
python3 abort.py      # Stop rotation

# Shutter operations
python3 open.py       # Open shutter
python3 close.py      # Close shutter

# Disconnect
python3 disconnect.py
```

---

## ⚙️ Configuration Management

### Checking Current Configuration

```bash
cd /home/pi/indi_k8055_dome_driver

# View current config
cat indi_driver/dome_config.json

# Test configuration validity
python3 -c "
from indi_driver.lib.config import DomeConfig
config = DomeConfig('indi_driver/dome_config.json')
print('✅ Configuration valid')
print(f'Home position: {config.dome.home_position}°')
print(f'Mock mode: {config.hardware.mock_mode}')
"
```

### Common Configuration Adjustments

**Home Position Adjustment:**
```json
{
  "dome": {
    "home_position": 15.5    // Adjust based on calibration results
  }
}
```

**Position Accuracy Tuning:**
```json
{
  "dome": {
    "ticks_to_degrees": 0.95  // Adjust if positions are consistently off
  }
}
```

**Timeout Adjustments:**
```json
{
  "dome": {
    "max_rotation_time": 400  // Increase for slower domes
  }
}
```

---

## 🧪 Regular Testing

### Daily Operations Check

```bash
# Quick functionality test (2 minutes)
export DOME_TEST_MODE=hardware
make test-hardware-safe
```

**What This Tests:**
- Hardware connectivity
- Basic movement (2-5 seconds)
- Emergency abort functionality
- Weather safety systems

### Weekly Comprehensive Test

```bash
# Complete system validation (10-15 minutes)
export DOME_TEST_MODE=hardware
make test-hardware-sequence
```

**What This Tests:**
- Full rotation capabilities
- Position accuracy
- Homing repeatability
- Shutter operations (if applicable)
- Error handling and recovery

### Monthly Calibration Check

```bash
# Calibration validation and data collection
make test-calibrate
```

**Review Results:**
- Check position accuracy remains within ±2°
- Verify home position repeatability
- Monitor rotation timing for performance changes

---

## 📊 Monitoring and Logs

### Status Monitoring

```bash
# Real-time dome status
watch -n 5 'cd /home/pi/indi_k8055_dome_driver/indi_driver/scripts && python3 status.py'

# Detailed status with debug info
python3 -c "
from indi_driver.lib.config import DomeConfig
from indi_driver.lib.dome import Dome
config = DomeConfig('indi_driver/dome_config.json')
dome = Dome(config)
dome.print_status()
"
```

### Log Files

Monitor these locations for system health:
- **INDI Logs**: Check INDI server output for connection issues
- **System Logs**: `dmesg | grep -i usb` for K8055 USB status
- **Dome Debug**: Enable debug mode in configuration for detailed logging

---

## 🌧️ Weather Considerations

### Rain Safety

The system automatically detects rain conditions:

```bash
# Check weather status
python3 -c "
import os
raining = os.getenv('WEATHER_RAINING', 'false').lower() == 'true'
print(f'Rain status: {\"Raining\" if raining else \"Clear\"}')
"
```

**Rain Behavior:**
- **Rotation**: Continues normally (safe in rain)
- **Shutter**: Blocked to prevent water entry
- **Override**: Set `SHUTTER_RAIN_OVERRIDE=true` if shutter operation required

### Wind and Other Conditions

For extreme weather, stop all operations:
```bash
# Emergency weather shutdown
cd /home/pi/indi_k8055_dome_driver/indi_driver/scripts
python3 abort.py      # Stop any motion
python3 close.py      # Close shutter
python3 park.py       # Move to home position
python3 disconnect.py # Disconnect from hardware
```

---

## 🔧 Maintenance

### Regular Maintenance Tasks

**Weekly:**
- Check USB cable connections
- Verify motor power supplies
- Test emergency stop functionality
- Run comprehensive test suite

**Monthly:**
- Clean limit switch contacts
- Check dome rotation mechanics
- Verify shutter operation smoothness
- Update calibration if needed

**Quarterly:**
- Review and update configuration
- Check for software updates
- Backup configuration files
- Deep clean K8055 connections

### Backup Important Files

```bash
# Backup configuration
cp indi_driver/dome_config.json dome_config_backup_$(date +%Y%m%d).json

# Backup calibration data (if you've customized it)
tar czf dome_backup_$(date +%Y%m%d).tar.gz \
    indi_driver/dome_config.json \
    indi_driver/scripts/
```

---

## 🚨 Emergency Procedures

### Immediate Stop

**If anything goes wrong:**
1. **Physical Emergency Stop**: Use hardware emergency stop if available
2. **Software Abort**: Click "Abort" in INDI client
3. **Script Abort**: Run `python3 abort.py` in scripts directory
4. **Power Disconnect**: Cut motor power if software stops don't work

### Lost Communication

**If dome stops responding:**
1. Check USB connection to K8055
2. Check motor power supplies
3. Restart INDI server: `sudo systemctl restart indi`
4. Reboot Raspberry Pi if needed
5. Switch to manual dome control if available

### Position Lost

**If dome position becomes unknown:**
1. Run `python3 park.py` to home the dome
2. Check home switch operation
3. Recalibrate if home position has drifted
4. Verify encoder/position system if applicable

---

## 🎯 Optimization Tips

### Performance Tuning

**For Faster Operations:**
- Decrease timeouts in configuration (but maintain safety margins)
- Ensure motor power supplies are adequate
- Check for mechanical friction points

**For Better Accuracy:**
- Run monthly calibration tests
- Adjust `ticks_to_degrees` based on position data
- Verify home switch repeatability

**For Reliability:**
- Use quality USB cables
- Ensure stable power supplies
- Keep connections clean and secure

---

## 🔗 Integration with Observatory Systems

### INDI/Ekos Integration

**Sequence Planning:**
- Dome automatically follows telescope in INDI/Ekos
- Configure dome following in Ekos mount module
- Set appropriate dome ahead/behind offset for your setup

**Automated Operations:**
- Dome opens/closes with observing sequences
- Park/unpark integrated with mount operations
- Emergency shutdown triggers dome close and park

### Weather Station Integration

Connect weather monitoring:
- Set environment variables based on weather station data
- Integrate rain sensor with `WEATHER_RAINING` variable
- Add wind monitoring for additional safety

---

*This guide covers typical day-to-day operations. For installation help, see the [Installation Guide](Installation_Guide.md). For problems, consult the [Troubleshooting Guide](Troubleshooting_Guide.md). For configuration variables, see [Environment Variables](Environment_Variables.md).*
