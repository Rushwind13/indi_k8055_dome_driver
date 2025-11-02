# INDI K8055 Dome Driver

**Self-contained INDI dome driver for Velleman K8055-based observatory dome controllers.**

## Structure

```
indi_driver/
├── scripts/              # INDI implementation (the 11 scripts)
│   ├── connect.py        # Test hardware connection
│   ├── disconnect.py     # Safe shutdown
│   ├── status.py         # Report dome status
│   ├── open.py           # Open shutter
│   ├── close.py          # Close shutter
│   ├── park.py           # Move to home + close
│   ├── unpark.py         # Prepare for operations
│   ├── goto.py           # Move to azimuth
│   ├── move_cw.py        # Start CW rotation
│   ├── move_ccw.py       # Start CCW rotation
│   └── abort.py          # Emergency stop
├── lib/                  # Library components
│   ├── dome.py           # Core dome control class
│   ├── config.py         # Configuration loader
│   └── pyk8055_wrapper.py # K8055 hardware interface
├── dome_config.json.example # Configuration template
└── requirements.txt      # Dependencies (none for mock mode)
```

## Quick Setup

1. **Point INDI dome_script driver to the scripts directory**:
   ```
   Script Folder: /path/to/indi_driver/scripts
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

2. **Configure hardware** (optional - uses safe defaults):
   ```bash
   cp dome_config.json.example dome_config.json
   # Edit dome_config.json for your hardware
   ```

3. **Test the driver**:
   ```bash
   python scripts/connect.py && echo "SUCCESS"
   python scripts/status.py
   ```

## Architecture

```
INDI dome_script → scripts/ → lib/dome.py → lib/pyk8055_wrapper.py → K8055 Hardware
```

## Modes

- **Mock Mode** (default): Safe operation without hardware
- **Hardware Mode**: Real K8055 operations (requires libk8055 on Raspberry Pi)

This is a complete, self-contained INDI dome driver. Copy this entire directory to deploy.
