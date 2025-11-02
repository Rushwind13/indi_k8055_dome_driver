#!/usr/bin/env python3
"""
Quick validation script to test the BDD test suite setup.
This script verifies that all components are properly configured.
"""

import os
import sys
from pathlib import Path


def check_file_structure():
    """Check that all required files exist."""
    print("📁 Checking file structure...")

    test_dir = Path(__file__).parent
    required_files = [
        "features/dome_startup_shutdown.feature",
        "features/dome_rotation.feature",
        "features/dome_home.feature",
        "features/shutter_operations.feature",
        "features/telemetry_monitoring.feature",
        "features/error_handling.feature",
        "steps/common_steps.py",
        "steps/error_handling_steps.py",
        "steps/startup_shutdown_steps.py",
        "environment.py",
        "run_tests.py",
        "requirements.txt",
        "README.md",
    ]

    missing_files = []
    for file_path in required_files:
        full_path = test_dir / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")

    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False

    print("  ✅ All required files present")
    return True


def check_imports():
    """Check that dome modules can be imported."""
    print("\n🔧 Checking dome module imports...")

    # Add parent directory to path
    test_dir = Path(__file__).parent
    parent_dir = test_dir.parent
    sys.path.insert(0, str(parent_dir))

    try:
        from dome import Dome

        print("  ✅ dome.Dome imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import dome.Dome: {e}")
        return False

    try:
        from config import load_config

        print("  ✅ config.load_config imported successfully")
    except ImportError as e:
        print(f"  ❌ Failed to import config.load_config: {e}")
        return False

    return True


def check_test_dependencies():
    """Check if test dependencies are available."""
    print("\n📦 Checking test dependencies...")

    # Check behave
    try:
        import behave

        print(f"  ✅ behave {behave.__version__} available")
    except ImportError:
        print("  ❌ behave not available")
        print("     Install with: pip install behave")
        return False

    # Check mock (usually built-in with Python 3.3+)
    try:
        from unittest.mock import Mock

        print("  ✅ unittest.mock available")
    except ImportError:
        print("  ❌ unittest.mock not available")
        return False

    return True


def test_dome_initialization():
    """Test basic dome initialization."""
    print("\n🔭 Testing dome initialization...")

    try:
        # Add parent directory to path
        test_dir = Path(__file__).parent
        parent_dir = test_dir.parent
        sys.path.insert(0, str(parent_dir))

        from config import load_config

        from dome import Dome

        # Load config with smoke test mode
        config = load_config()
        config["smoke_test"] = True

        # Create dome instance
        dome = Dome(config)

        print("  ✅ Dome instance created successfully")
        print(f"  📊 Smoke test mode: {config.get('smoke_test', False)}")
        print(f"  📍 Current azimuth: {getattr(dome, 'current_azimuth', 'Unknown')}")

        return True

    except Exception as e:
        print(f"  ❌ Dome initialization failed: {e}")
        return False


def test_feature_file_syntax():
    """Basic syntax check of feature files."""
    print("\n📋 Checking feature file syntax...")

    test_dir = Path(__file__).parent
    features_dir = test_dir / "features"

    if not features_dir.exists():
        print("  ❌ Features directory not found")
        return False

    feature_files = list(features_dir.glob("*.feature"))
    if not feature_files:
        print("  ❌ No feature files found")
        return False

    for feature_file in feature_files:
        try:
            with open(feature_file, "r") as f:
                content = f.read()
                if "Feature:" not in content:
                    print(f"  ❌ {feature_file.name}: No 'Feature' declaration found")
                    return False
                if "Scenario:" not in content:
                    print(f"  ❌ {feature_file.name}: No 'Scenario' found")
                    return False
                print(f"  ✅ {feature_file.name}: Basic syntax OK")
        except Exception as e:
            print(f"  ❌ {feature_file.name}: Error reading file: {e}")
            return False

    return True


def run_quick_test():
    """Run a quick smoke test to verify everything works."""
    print("\n🧪 Running quick smoke test...")

    try:
        test_dir = Path(__file__).parent

        # Change to test directory
        original_cwd = os.getcwd()
        os.chdir(test_dir)

        # Set environment for smoke test
        env = os.environ.copy()
        env["DOME_TEST_MODE"] = "smoke"

        # Run behave with just one feature
        import subprocess

        # Find a feature file to test
        features_dir = Path("features")
        feature_files = list(features_dir.glob("*.feature"))

        if not feature_files:
            print("  ❌ No feature files found for testing")
            return False

        test_feature = feature_files[0]  # Use first feature

        cmd = ["python", "-m", "behave", "--dry-run", str(test_feature)]

        result = subprocess.run(
            cmd, env=env, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            print(f"  ✅ Dry run of {test_feature.name} successful")
            print("  📊 Test framework is properly configured")
            return True
        else:
            print(f"  ❌ Dry run failed: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("  ❌ Test timed out")
        return False
    except FileNotFoundError:
        print("  ❌ behave command not found")
        return False
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False
    finally:
        os.chdir(original_cwd)


def main():
    """Main validation function."""
    print("🔍 DOME CONTROL SYSTEM - BDD TEST SUITE VALIDATION")
    print("=" * 60)

    all_checks_passed = True

    # Run all validation checks
    checks = [
        check_file_structure,
        check_imports,
        check_test_dependencies,
        test_dome_initialization,
        test_feature_file_syntax,
        run_quick_test,
    ]

    for check in checks:
        if not check():
            all_checks_passed = False

    print("\n" + "=" * 60)

    if all_checks_passed:
        print("✅ ALL VALIDATION CHECKS PASSED!")
        print("\n🚀 Ready to run tests:")
        print("   python test/run_tests.py                    # Run smoke tests")
        print("   python test/run_tests.py --list-features    # List features")
        print("   python test/run_tests.py --help             # Show help")
        print("\n⚠️  For hardware tests:")
        print(
            "   python test/run_tests.py --mode hardware    # CAUTION: Real hardware!"
        )
    else:
        print("❌ SOME VALIDATION CHECKS FAILED!")
        print("\n🔧 To fix issues:")
        print("   pip install -r test/requirements.txt        # Install dependencies")
        print(
            "   python test/run_tests.py --install-deps     # Create requirements.txt"
        )

    return all_checks_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
