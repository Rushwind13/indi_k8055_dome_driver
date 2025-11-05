# INDI K8055 Dome Driver - Architecture

**Production-Ready Astronomical Dome Control System**

## Overview

The INDI K8055 Dome Driver provides comprehensive dome control for astronomical observatories using the Velleman K8055 USB interface board. The system implements INDI Dome Scripting Gateway compatibility with advanced features for reliable operation.

## System Architecture

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   INDI Server   │◄──►│   Dome Scripts   │◄──►│  Dome Library   │
│                 │    │  (entry points)  │    │   (dome.py)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                        ┌──────────────────┐    ┌─────────────────┐
                        │   Persistence    │◄──►│  K8055 Wrapper  │
                        │  (state mgmt)    │    │ (pyk8055_wrapper)│
                        └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │ Hardware Layer  │
                                                │ (K8055 + Dome)  │
                                                └─────────────────┘
```

### Hardware Interface

**K8055 USB Interface Board**
- **Digital Inputs (5)**: Home switch, encoder channels A & B
- **Digital Outputs (8)**: Motor control relays (rotation + shutter)
- **Analog I/O**: Reserved for future telemetry

**4-Relay Motor Control System**
- **Rotation Motor**: Direction relay + Enable relay
- **Shutter Motor**: Direction relay + Enable relay

### Software Architecture Principles

1. **Production Environment**: `indi_driver/` folder is standalone and plug-out ready
2. **Mock Development**: Full testing capability without hardware
3. **State Persistence**: Seamless operation across script invocations
4. **Non-blocking Operations**: Fast relay control with polling-based timing
5. **Safety-First Design**: Emergency stops, timeouts, and error recovery

## Key Features Implementation

### Advanced Motor Control (B1-B2)

**Non-Blocking Rotation Control**
- `start_rotation()`: Set relays and return immediately
- `stop_rotation()`: Clear relays with emergency stop capability
- **Bidirectional Logic**: Automatic shortest-path calculation
- **Relay Sequencing**: Direction first, then enable (20ms timing)

```python
# Example: Non-blocking 180-degree rotation
dome.rotation(180.0)  # Calculates direction, starts rotation
while dome.is_turning:
    time.sleep(dome.POLL)  # Non-blocking polling
# Automatically stops when target reached
```

### 2-Bit Gray Code Encoder System (C1)

**Quadrature Encoder Reading**
- **Gray Code States**: 4-state sequence for direction detection
- **CW Sequence**: 0→1→3→2→0 (00→01→11→10→00)
- **CCW Sequence**: 0→2→3→1→0 (00→10→11→01→00)
- **Speed Calculation**: Real-time degrees/second tracking

```python
# Enhanced encoder tracking with direction validation
dome.update_encoder_tracking()
print("Direction:", dome.encoder_direction)  # 'CW' or 'CCW'
print("Speed:", dome.encoder_speed, "deg/s")
```

### Optimized Home Switch Polling (C2)

**Fast Polling During Homing**
- **Dynamic Rates**: 50ms fast polling vs 500ms normal
- **Signal Validation**: 100ms debounce threshold for noise rejection
- **Speed Tracking**: Maximum rotation speed monitoring

```python
# Enhanced homing with 10x faster polling
dome.home()  # Automatically switches to fast polling
# Polls at 50ms during homing, 500ms during normal operation
```

### Encoder Calibration System (C3)

**Automated Calibration**
- **Full Rotation Calibration**: Measures actual ticks per degree
- **Accuracy Validation**: Compares measured vs configured ratios
- **Error Detection**: Invalid transitions and signal quality issues
- **Automatic Recovery**: Error threshold-based reset

```python
# Automated encoder calibration
results = dome.calibrate_encoder_ticks_to_degrees()
print("Accuracy:", results['accuracy_percent'], "%")
if results['accuracy_percent'] < 90:
    print("Update config:", results['recommended_config'])
```

### State Persistence System

**Seamless State Management**
- **Position Tracking**: Maintains position across script invocations
- **Connection State**: Tracks hardware connection status
- **Operation State**: Preserves in-progress operations
- **Automatic Recovery**: Restores state on script startup

```python
# All scripts automatically save/restore state
from persistence import restore_state, save_state

dome = restore_state()  # Loads previous state
# ... perform operations ...
save_state(dome, "operation_name")  # Saves current state
```

## Configuration Management

### Production Configuration (`dome_config.json`)

```json
{
    "pins": {
        "encoder_a": 1,
        "encoder_b": 5,
        "home_switch": 2,
        "dome_rotate": 1,
        "dome_direction": 2,
        "shutter_move": 5,
        "shutter_direction": 6
    },
    "calibration": {
        "home_position": 225,
        "ticks_to_degrees": 4.0,
        "poll_interval": 0.5,
        "home_poll_fast": 0.05,
        "home_switch_debounce": 0.1,
        "encoder_error_threshold": 50,
        "encoder_calibration_timeout": 180.0
    },
    "hardware": {
        "mock_mode": false,
        "device_port": 0
    },
    "safety": {
        "emergency_stop_timeout": 2.0,
        "operation_timeout": 60.0,
        "max_rotation_time": 120.0,
        "max_shutter_time": 30.0
    }
}
```

### Key Configuration Features

- **Pin Mapping**: Complete K8055 pin assignments
- **Timing Parameters**: Polling rates and timeouts
- **Calibration Values**: Encoder ratios and thresholds
- **Safety Limits**: Operation timeouts and emergency stops
- **Development Support**: Mock mode for testing

## Safety and Reliability Features

### Emergency Stop System
- **Immediate Response**: 2-second emergency stop guarantee
- **All Scripts**: Every script can execute emergency stop
- **Hardware Override**: Direct relay control bypass

### Error Detection and Recovery
- **Encoder Errors**: Invalid transition detection and automatic reset
- **Connection Monitoring**: Hardware connection state tracking
- **Operation Timeouts**: Configurable limits for all operations
- **Graceful Degradation**: Continues operation despite minor errors

### Validation and Testing
- **Python 2.7 Validation**: Comprehensive production environment testing
- **Mock Mode Testing**: Full functionality without hardware
- **Integration Tests**: End-to-end operation validation
- **Hardware Tests**: Real hardware validation sequences

## Performance Optimizations

### Polling Optimizations
- **Fast Homing**: 10x faster polling during critical operations
- **Adaptive Rates**: Different polling rates for different operations
- **Efficient Loops**: Minimal CPU usage during polling

### Encoder Performance
- **Real-time Tracking**: Continuous speed and direction monitoring
- **Error Mitigation**: Automatic recovery from signal issues
- **Calibration Accuracy**: Sub-degree positioning accuracy

### Memory and State Management
- **Minimal Footprint**: Efficient state storage and retrieval
- **Fast Startup**: Quick state restoration on script startup
- **Clean Shutdown**: Proper state saving on script termination

## Development Environment

### Cross-Platform Development
- **Mac Development**: Full mock mode capability
- **Raspberry Pi Production**: Real hardware integration
- **Consistent API**: Same code works in both environments

### Testing Infrastructure
- **Mock Hardware**: Complete K8055 simulation
- **Validation Suite**: 7-test comprehensive validation
- **Hardware Tests**: Safe hardware validation sequences

## INDI Script Compatibility

### Required INDI Scripts

The system provides all required INDI Dome Scripting Gateway scripts:

1. **connect.py** - Establish dome connection and save initial state
2. **disconnect.py** - Clean disconnection with state preservation
3. **status.py** - Report current dome status and position
4. **goto.py** - Move dome to specified azimuth position
5. **move_cw.py** - Start clockwise rotation
6. **move_ccw.py** - Start counter-clockwise rotation
7. **abort.py** - Emergency stop all dome operations
8. **park.py** - Move to home position and close shutter
9. **unpark.py** - Open shutter and prepare for operations
10. **open.py** - Open shutter only
11. **close.py** - Close shutter only

### INDI Integration Features
- **Status Reporting**: Real-time position and state information
- **Error Handling**: Proper INDI error code responses
- **Timeout Management**: Configurable operation timeouts
- **State Persistence**: Maintains state across INDI reconnections

---

**Architecture Status**: Production Ready
**Last Updated**: November 4, 2025
**Implementation**: Complete with advanced features
