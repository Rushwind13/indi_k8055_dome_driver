# INDI K8055 Dome Driver Scripts

The 11 INDI wrapper scripts that serve as the official interface between INDI's dome_script driver and the K8055 dome hardware.

## Scripts

| Script | Function | Arguments |
|--------|----------|-----------|
| `connect.py` | Test hardware connection | None |
| `disconnect.py` | Safe shutdown | None |
| `status.py` | Report dome status | Optional: file path |
| `open.py` | Open shutter | None |
| `close.py` | Close shutter | None |
| `park.py` | Move to home + close | None |
| `unpark.py` | Prepare for operations | None |
| `goto.py` | Move to azimuth | Azimuth (degrees) |
| `move_cw.py` | Start CW rotation | None |
| `move_ccw.py` | Start CCW rotation | None |
| `abort.py` | Emergency stop | None |

## Usage

### Production Mode (Silent)
```bash
python scripts/connect.py          # No output on success
python scripts/status.py           # Outputs: "0 0 0.0"
python scripts/goto.py 90.0        # No output on success
```

### Debug Mode (Verbose)
```bash
python scripts/connect.py --verbose     # Shows initialization details
python scripts/status.py --verbose      # Shows status calculation
python scripts/goto.py --verbose 90.0   # Shows movement progress
```

## INDI Integration

These scripts are called by INDI's `dome_script.cpp` driver with specific argument patterns:
- `status.py` may receive a temp file path for output
- `goto.py` receives azimuth as a float argument
- All others receive no arguments (except `--verbose` for testing)

All scripts follow INDI contract: exit code 0 for success, 1 for failure, silent operation except status output.
