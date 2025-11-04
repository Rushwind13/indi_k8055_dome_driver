# Python 2.7 Validation

This directory contains the Python 2.7 validation suite for the INDI K8055 dome driver.

## Files

- **`validate_py27.py`** - Consolidated validation suite for Python 2.7 compatibility

## Usage

### Quick Validation
```bash
source venv_py27/bin/activate
python test/python2/validate_py27.py
```

### Verbose Mode
```bash
python test/python2/validate_py27.py --verbose
```

### Persistence Tests Only
```bash
python test/python2/validate_py27.py --persistence-only
```

## Make Targets

Alternatively, use the integrated Make targets:

```bash
make test-py27                # All validation tests
make test-py27-verbose        # Verbose output
make test-py27-persistence    # Persistence tests only
make test-py27-full          # Complete validation with linting
```

## Test Coverage

The validation suite covers:
1. **Import Tests** - Core module compatibility
2. **Dome Creation** - Object instantiation and basic functionality  
3. **State Persistence** - Configuration and sensor state management
4. **Script Integration** - INDI script compatibility
5. **Python 2.7 Compatibility** - Version-specific features

## Environment

Requires Python 2.7 virtual environment with required packages. Use `make setup-py27` to create the environment automatically.

## Expected Results

All tests should pass on Python 2.7 environments:

- ✅ All modules import without errors
- ✅ Dome objects can be created and operated
- ✅ State persistence works across script executions
- ✅ INDI scripts have persistence integration
- ✅ Code is compatible with Python 2.7 syntax

## Troubleshooting

- **Import errors**: Ensure Python 2.7 environment is activated and packages installed
- **Hardware errors**: Tests run in mock mode by default
- **Persistence errors**: Check file permissions and temp directory access