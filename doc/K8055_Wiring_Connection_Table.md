# K8055 Wiring Connection Table

**INDI K8055 Dome Driver - Pin Assignment Documentation**

This document provides the complete mapping of K8055 interface board pins to physical dome hardware functions.

## 📋 K8055 Interface Board Overview

The Velleman K8055 USB interface board provides:
- **Digital Inputs**: 5 channels (1-5) - TTL level inputs for switches/sensors
- **Digital Outputs**: 8 channels (1-8) - Open collector outputs for relays/motors
- **Analog Inputs**: 2 channels (1-2) - 0-255 range for analog sensors
- **Analog Outputs**: 2 channels (1-2) - 0-255 range for analog control

## 🔌 Current Pin Configuration (from dome_config.json)

### Digital Inputs (1-5) - Sensors and Switches
| Pin | Function | Description | Usage |
|-----|----------|-------------|-------|
| 1 | **encoder_a** | Encoder Channel A | 2-bit Gray Code position feedback |
| 2 | **home_switch** | Home Position Switch | Triggers when dome reaches home position |
| 3 | *unused* | Available | Could be used for safety interlocks |
| 4 | **direction_telemetry** | Rotation Direction Feedback | Wired to DO2 for direction confirmation |
| 5 | **encoder_b** | Encoder Channel B | 2-bit Gray Code position feedback |

### Digital Outputs (1-8) - Relay Control
| Pin | Function | Description | Relay Type | Motor |
|-----|----------|-------------|------------|-------|
| 1 | **dome_rotate** | Dome Rotation Enable | Enable Relay | Rotation Motor |
| 2 | **dome_direction** | Dome Rotation Direction | Direction Relay | Rotation Motor |
| 3 | *unused* | Available | - | - |
| 4 | *unused* | Available | - | - |
| 5 | **shutter_move** | Shutter Movement Enable | Enable Relay | Shutter Motor |
| 6 | **shutter_direction** | Shutter Direction Control | Direction Relay | Shutter Motor |
| 7 | *unused* | Available | - | - |
| 8 | *unused* | Available | - | - |

### Analog Inputs (1-2) - Not Currently Used
| Pin | Function | Description | Range | Usage |
|-----|----------|-------------|-------|-------|
| 1 | *unused* | Available | 0-255 | Could be used for analog sensors |
| 2 | *unused* | Available | 0-255 | Could be used for analog sensors |

### Analog Outputs (1-2) - Not Currently Used
| Pin | Function | Description | Range | Usage |
|-----|----------|-------------|-------|-------|
| 1 | *unused* | Available | 0-255 | Could be used for analog control |
| 2 | *unused* | Available | 0-255 | Could be used for analog control |

## ⚡ Relay Control Logic

The dome uses **4 relays total** for motor control:

### Rotation Motor Control
- **Enable Relay** (dome_rotate, Pin 1): ON = motor can run, OFF = motor stopped
- **Direction Relay** (dome_direction, Pin 2): Controls CW/CCW rotation
  - `dome_direction = OFF (False)` → **Clockwise (CW)**
  - `dome_direction = ON (True)` → **Counter-Clockwise (CCW)**
- **Direction Telemetry** (Pin 4): Reads back actual direction state from DO2
  - Allows verification that commanded direction matches actual relay state

### Shutter Motor Control
- **Enable Relay** (shutter_move, Pin 5): ON = motor can run, OFF = motor stopped
- **Direction Relay** (shutter_direction, Pin 6): Controls OPEN/CLOSE direction
  - `shutter_direction = OFF (False)` → **Opening Direction**
  - `shutter_direction = ON (True)` → **Closing Direction**

## 🔄 2-Bit Gray Code Encoder

The rotation encoder provides position feedback using 2-bit Gray Code:

| Encoder A | Encoder B | Gray Code State | Rotation Direction |
|-----------|-----------|-----------------|-------------------|
| 0 | 0 | State 00 | - |
| 0 | 1 | State 01 | Transitioning |
| 1 | 1 | State 11 | - |
| 1 | 0 | State 10 | Transitioning |

**Direction Detection**: Based on state transition sequence
- **CW**: 00 → 01 → 11 → 10 → 00 (repeating)
- **CCW**: 00 → 10 → 11 → 01 → 00 (repeating)

## 🏠 Home Switch Operation

- **Pin**: Digital Input 2 (home_switch)
- **Active State**: HIGH (1) when dome is at home position
- **Inactive State**: LOW (0) when dome is not at home position
- **Usage**: Used for homing operations and position reset

## 🚨 Safety Considerations

### Pin Conflicts to Avoid
- **No conflicts found** in current configuration
- Digital inputs (1-5) and digital outputs (1-8) are separate ranges
- encoder_a (DI1) and dome_rotate (DO1) can safely use the same number

### Unused Pins Available for Enhancement
- **Digital Input 3**: Could add safety interlocks or additional sensors
- **Digital Outputs 3, 4, 7, 8**: Could add additional safety relays
- **All Analog I/O**: Currently unused, available for sensors/control

### Critical Wiring Requirements
1. **Relay Sequencing**: Set direction BEFORE enabling motor
2. **Emergency Stop**: Disable all motor enable relays immediately
3. **Power Safety**: Ensure relays are "normally off" (fail-safe)
4. **Encoder Protection**: Encoder inputs should be optically isolated
5. **Direction Telemetry**: DO2 is wired to DI4 for direction confirmation

## 🔧 Configuration Errors in Code

**Note**: The following references in the code are **ERRORS** and should be ignored:
- `shutter_upper_limit` - No shutter limit telemetry exists
- `shutter_lower_limit` - No shutter limit telemetry exists

The dome design uses **fixed timing with automatic limit switch cutoff** for shutter operations, not telemetry feedback.

## 📐 Physical Wiring Diagram

```
K8055 USB Interface Board
========================

Digital Inputs (1-5):
DI1 ──► Encoder Channel A
DI2 ──► Home Switch
DI3 ──► [Available]
DI4 ──► Direction Telemetry (wired to DO2)
DI5 ──► Encoder Channel B

Digital Outputs (1-8):
DO1 ──► Rotation Enable Relay ──► Rotation Motor Power
DO2 ──► Rotation Direction Relay ──► Rotation Motor Direction
    └──► (also wired to DI4 for telemetry feedback)
DO3 ──► [Available]
DO4 ──► [Available]
DO5 ──► Shutter Enable Relay ──► Shutter Motor Power
DO6 ──► Shutter Direction Relay ──► Shutter Motor Direction
DO7 ──► [Available]
DO8 ──► [Available]

Analog I/O:
AI1 ──► [Available]
AI2 ──► [Available]
AO1 ──► [Available]
AO2 ──► [Available]
```

## 🎯 Validation Checklist

- [x] No pin conflicts between inputs and outputs
- [x] All configured pins within valid ranges (DI:1-5, DO:1-8)
- [x] Relay control logic documented (direction vs enable)
- [x] Encoder Gray Code mapping documented
- [x] Home switch operation defined
- [x] Shutter limit telemetry errors identified
- [x] Available pins documented for future enhancement

---

**Last Updated:** November 4, 2025
**Status:** Pin mapping complete - ready for hardware validation
**Next Action:** Validate pin configuration with actual hardware using k8055_pin_tester.py
