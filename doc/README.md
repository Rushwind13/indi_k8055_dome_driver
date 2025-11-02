# Documentation Scripts

The `doc/` directory contains 3 specialized Python scripts that demonstrate different aspects of the dome system. Each serves a specific purpose and audience.

## Script Overview

| Script | Purpose | When to Use | Audience |
|--------|---------|-------------|----------|
| `demo_hardware_modes.py` | Interactive wrapper demonstration | Learning/testing wrapper behavior | Developers, users |
| `enhanced_dome_example.py` | Hardware detection patterns | Implementing smart initialization | Advanced developers |
| `production_setup_guide.py` | Raspberry Pi deployment guide | First-time production setup | System administrators |

## Individual Scripts

### `demo_hardware_modes.py`
**Purpose**: Educational demonstration of mock vs hardware modes
**Safe to run**: Always (uses mock mode only)
**Use cases**:
- Learning how the wrapper system works
- Testing configuration options
- Demonstrating to other developers
- Understanding error handling

**Run with**: `python doc/demo_hardware_modes.py`

### `enhanced_dome_example.py`
**Purpose**: Advanced dome initialization with automatic hardware detection
**Use cases**:
- Implementing environment-aware dome setup
- Adding fallback mechanisms to dome.py
- Understanding deployment automation patterns
- Reference for smart hardware detection

**Run with**: `python doc/enhanced_dome_example.py`

### `production_setup_guide.py`
**Purpose**: Complete Raspberry Pi setup and deployment reference
**Use cases**:
- First-time production hardware deployment
- Setting up libk8055 dependencies
- Understanding production vs development differences
- Configuring real K8055 integration

**Run with**: `python doc/production_setup_guide.py`

## Non-Redundant Behavior Confirmed

✅ **`demo_hardware_modes.py`**: Interactive demonstrations with step-by-step explanations
✅ **`enhanced_dome_example.py`**: Configuration scenarios and automatic detection examples
✅ **`production_setup_guide.py`**: Installation commands and deployment workflows

Each script provides unique value and can be run independently without conflicts.
