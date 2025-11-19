# Copilot Instructions for INDI K8055 Dome Driver

## Project Overview
- **Purpose:** INDI-compliant dome driver for Velleman K8055-based observatory domes, supporting both Python 2.7 and 3.x, with robust state persistence and hardware/mock abstraction.
- **Key Directories:**
  - `indi_driver/scripts/` — 11 INDI driver scripts (main entrypoints)
  - `indi_driver/lib/` — Core dome logic (`dome.py`), hardware abstraction (`pyk8055_wrapper.py`), config management (`config.py`)
  - `indi_driver/python2/` — Python 2.7-compatible scripts and libraries
  - `test/` — Full test suite (unit, integration, BDD, smoke)
  - `doc/` — User and developer documentation, deployment guides, and demo scripts

## Architecture & Patterns
- **Data Flow:**
  - INDI dome_script → `scripts/*.py` → `lib/dome.py` → `lib/pyk8055_wrapper.py` → K8055 hardware
  - Python 2.7 support: use `indi_driver/python2/scripts/` and `indi_driver/python2/lib/`
- **Mock vs Hardware:**
  - Mock mode (for dev/CI): set `DOME_TEST_MODE=smoke` (no hardware required)
  - Hardware mode (default): real K8055 operations (requires `libk8055`)
- **Configuration:**
  - All settings in `indi_driver/dome_config.json` (copy from `.example`)
  - Pin assignments, calibration, safety timeouts, and device port are required fields

## Developer Workflows
- **Testing:**
  - Run all tests: `python test/run_tests.py`
  - Unit only: `python test/run_tests.py --unit`
  - Integration only: `python test/run_tests.py --integration-only`
  - Hardware mode: `python test/run_tests.py --mode hardware -y` (CAUTION: moves real hardware)
  - Python 2.7 validation: `make test-py27`
- **Build/Deploy:**
  - No build step required; copy directory to deploy
  - For Python 2.7, copy `indi_driver/python2/` to target
- **Troubleshooting:**
  - Use `python scripts/status.py --verbose` for diagnostics
  - Enable mock mode for safe testing: `export DOME_TEST_MODE=smoke`

## Project Conventions
- **No f-strings or modern Python 3 features in Python 2.7 code**
- **State persistence:** All dome state (position, encoders, home, shutter) is preserved between script executions
- **Safety:** Hardware mode includes strict timeouts and emergency stop logic
- **Test suite:** BDD features in `test/integration/features/`, step definitions in `test/integration/steps/`
- **Documentation:** All guides and architecture docs in `doc/`

## Integration Points
- **INDI:** Communicates via dome_script interface (see Quick Start in root `README.md`)
- **K8055:** Hardware abstraction in `pyk8055_wrapper.py` (mocked in dev mode)
- **Environment variables:** `DOME_TEST_MODE`, `DOME_CONFIG_FILE` (custom config path)

## Examples
- **Test connection:** `python scripts/connect.py && echo "SUCCESS"`
- **Run smoke tests:** `python test/run_tests.py --mode smoke`
- **Deploy Python 2.7:** `cp -r indi_driver/python2/ /target/path/`

---

**For more, see:**
- `README.md` (root, indi_driver/, test/)
- `doc/Installation_Guide.md`, `doc/User_Guide.md`, `doc/Architecture.md`
- `test/README.md` for test details
