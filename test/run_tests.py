#!/usr/bin/env python3
"""
Dome Control System Test Runner.

This script provides a comprehensive test suite runner that includes:
- Integration tests for the pyk8055_wrapper
- Documentation script validation
- BDD tests with behave
- Pre-commit hook validation

Usage:
    python run_tests.py                    # Run all tests (integration + BDD smoke)
    python run_tests.py --mode smoke       # Run smoke tests explicitly
    python run_tests.py --mode hardware    # Run hardware tests (CAUTION!)
    python run_tests.py --integration-only # Run only integration tests
    python run_tests.py --doc-only         # Run only doc script tests
    python run_tests.py --bdd-only         # Run only BDD tests
    python run_tests.py --feature rotation # Run specific BDD feature
    python run_tests.py --all              # Run everything with pre-commit
    python run_tests.py --help             # Show help
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_integration_tests():
    """Run integration tests."""
    print("🔹 Running Integration Tests...")
    print("-" * 60)
    try:
        # Change to parent directory to run integration tests
        original_cwd = os.getcwd()
        os.chdir(os.path.dirname(os.path.dirname(__file__)))

        result = subprocess.run(
            [sys.executable, "test/test_wrapper_integration.py"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            print(result.stdout)
            print("✅ Integration tests passed")
            return True
        else:
            print("❌ Integration tests failed:")
            print(f"stdout: {result.stdout}")
            print(f"stderr: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Integration tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False
    finally:
        os.chdir(original_cwd)


def run_unit_tests():
    """Run unit tests with pytest."""
    print("🔹 Running Unit Tests...")
    print("-" * 60)
    try:
        # Check if pytest is available
        try:
            import pytest
        except ImportError:
            print("⚠️  pytest not available, skipping unit tests")
            print("   Install with: pip install pytest")
            return True  # Don't fail if pytest not available

        # Change to parent directory to run unit tests
        original_cwd = os.getcwd()
        os.chdir(os.path.dirname(os.path.dirname(__file__)))

        # Run pytest on unit test files
        unit_test_files = [
            "test/test_dome_units.py",
            "test/test_safety_critical.py",
        ]

        all_passed = True
        for test_file in unit_test_files:
            if os.path.exists(test_file):
                print(f"  Running {test_file}...")
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", test_file, "-v"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                if result.returncode == 0:
                    print(f"    ✅ {test_file} passed")
                    # Show summary of tests run
                    lines = result.stdout.split("\n")
                    for line in lines:
                        if "passed" in line and ("failed" in line or "error" in line):
                            print(f"    📊 {line.strip()}")
                        elif line.startswith("PASSED") or line.startswith("FAILED"):
                            print(f"    {line.strip()}")
                else:
                    print(f"    ❌ {test_file} failed:")
                    print(f"      stderr: {result.stderr[:200]}...")
                    all_passed = False
            else:
                print(f"  ⚠️  {test_file} not found, skipping...")

        if all_passed:
            print("✅ Unit tests passed")
        else:
            print("❌ Some unit tests failed")

        return all_passed

    except subprocess.TimeoutExpired:
        print("❌ Unit tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False
    finally:
        os.chdir(original_cwd)


def run_doc_script_tests():
    """Run the documentation script tests."""
    script_dir = Path(__file__).parent
    test_file = script_dir / "test_doc_scripts.py"

    print("\n🔹 Running Documentation Script Tests...")
    print("-" * 60)

    if not test_file.exists():
        print(f"❌ Doc script test file not found: {test_file}")
        return False

    try:
        result = subprocess.run([sys.executable, str(test_file)], cwd=script_dir.parent)
        if result.returncode == 0:
            print("✅ Documentation script tests passed")
            return True
        else:
            print("❌ Documentation script tests failed")
            return False
    except Exception as e:
        print(f"❌ Error running documentation script tests: {e}")
        return False


def run_pre_commit_checks():
    """Run pre-commit hooks for code quality."""
    print("\n🔹 Running Pre-commit Checks...")
    print("-" * 60)

    try:
        # Check if pre-commit is available
        result = subprocess.run(
            ["pre-commit", "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            print("⚠️  pre-commit not available, skipping code quality checks")
            return True
    except FileNotFoundError:
        print("⚠️  pre-commit not installed, skipping code quality checks")
        print("   Install with: pip install pre-commit")
        return True

    try:
        # Run pre-commit on all files
        result = subprocess.run(
            ["pre-commit", "run", "--all-files"], cwd=Path(__file__).parent.parent
        )
        if result.returncode == 0:
            print("✅ Pre-commit checks passed")
            return True
        else:
            print("❌ Pre-commit checks failed")
            return False
    except Exception as e:
        print(f"❌ Error running pre-commit checks: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []

    # Check behave for BDD tests
    try:
        import behave
    except ImportError:
        missing_deps.append("behave")

    # Check mock (usually built-in with Python 3.3+)
    try:
        from unittest.mock import Mock
    except ImportError:
        missing_deps.append("mock")

    # Check pre-commit for code quality
    try:
        import subprocess

        result = subprocess.run(
            ["pre-commit", "--version"], capture_output=True, text=True
        )
        if result.returncode != 0:
            missing_deps.append("pre-commit")
    except (FileNotFoundError, subprocess.SubprocessError):
        missing_deps.append("pre-commit")

    # Check pytest for unit tests (optional)
    try:
        import pytest
    except ImportError:
        print("ℹ️  pytest not available (optional for unit tests)")

    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        return False

    print("✅ All required dependencies available")
    return True


def create_requirements_file():
    """Create requirements.txt for test dependencies."""
    requirements_content = """# Dome Control System Test Dependencies
behave>=1.2.6
mock>=4.0.3
"""

    requirements_path = Path(__file__).parent / "requirements.txt"
    with open(requirements_path, "w") as f:
        f.write(requirements_content)

    print(f"📄 Created {requirements_path}")
    print("   Install test dependencies with: pip install -r test/requirements.txt")


def run_behave_tests(args):
    """Run the behave test suite with specified arguments."""
    script_dir = Path(__file__).parent

    # Set environment variables
    env = os.environ.copy()
    env["DOME_TEST_MODE"] = args.mode

    # Ensure behave process can import project modules in indi_driver/lib
    # (some test steps import `config`, `dome`, etc.)
    lib_path = str(script_dir.parent / "indi_driver" / "lib")
    existing_py = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = lib_path + (os.pathsep + existing_py if existing_py else "")

    # Build behave command
    cmd = ["python", "-m", "behave"]

    # Add feature filter if specified
    if args.feature:
        feature_path = script_dir / "features" / f"{args.feature}.feature"
        if feature_path.exists():
            cmd.append(str(feature_path))
        else:
            available_features = list((script_dir / "features").glob("*.feature"))
            feature_names = [f.stem for f in available_features]
            print(f"❌ Feature '{args.feature}' not found")
            print(f"   Available features: {', '.join(feature_names)}")
            return False
    else:
        # Run all features
        cmd.append(str(script_dir / "features"))

    # Add tag filter if specified
    if args.tag:
        cmd.extend(["--tags", args.tag])

    # Add verbosity options
    if args.verbose:
        cmd.append("--verbose")

    # Add format options
    if args.format:
        cmd.extend(["--format", args.format])

    # Add output file if specified
    if args.output:
        cmd.extend(["--outfile", args.output])

    # Change to test directory
    original_cwd = os.getcwd()
    os.chdir(script_dir)

    try:
        print(f"🚀 Running command: {' '.join(cmd)}")
        print(f"📁 Working directory: {script_dir}")
        print(f"🔧 Test mode: {args.mode.upper()}")
        print("-" * 60)

        # Run behave
        result = subprocess.run(cmd, env=env)
        return result.returncode == 0

    except FileNotFoundError:
        print("❌ behave not found. Install with: pip install behave")
        return False
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return False
    finally:
        os.chdir(original_cwd)


def list_features():
    """List available test features."""
    script_dir = Path(__file__).parent
    features_dir = script_dir / "features"

    if not features_dir.exists():
        print("❌ Features directory not found")
        return

    features = list(features_dir.glob("*.feature"))
    if not features:
        print("❌ No feature files found")
        return

    print("📋 Available test features:")
    for feature in sorted(features):
        print(f"   • {feature.stem}")

        # Try to read feature description
        try:
            with open(feature, "r") as f:
                first_line = f.readline().strip()
                if first_line.startswith("Feature:"):
                    description = first_line[8:].strip()
                    print(f"     {description}")
        except Exception:
            pass
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Dome Control System Comprehensive Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Suites Available:
  Integration Tests    - Test pyk8055_wrapper functionality and dome integration
  Doc Script Tests     - Validate Python scripts in doc/ directory
  BDD Tests           - Behavior-driven tests with behave framework
  Pre-commit Checks   - Code quality and formatting validation

Examples:
  python run_tests.py                     # Run integration + BDD smoke tests
  python run_tests.py --all               # Run everything including pre-commit
  python run_tests.py --integration-only  # Run only integration tests
  python run_tests.py --doc-only          # Run only doc script tests
  python run_tests.py --bdd-only          # Run only BDD tests
  python run_tests.py --mode hardware     # Run hardware tests (CAUTION!)
  python run_tests.py --feature rotation  # Run specific BDD feature
  python run_tests.py --tag @smoke        # Run smoke-tagged BDD tests

Test Modes (for BDD tests):
  smoke    - Safe mode with no real hardware operations (default)
  hardware - Real hardware mode with actual dome movements (CAUTION!)

Notes:
  - Default behavior runs integration tests + BDD smoke tests
  - Hardware mode requires proper dome setup and safety precautions
  - Use --all for complete validation before commits/releases
  - Doc script tests ensure documentation examples work correctly
        """,
    )

    # Test suite selection
    parser.add_argument(
        "--all", action="store_true", help="Run all tests including pre-commit checks"
    )

    parser.add_argument(
        "--integration-only", action="store_true", help="Run only integration tests"
    )

    # Support both `--unit` (convenience) and `--unit-only` for compatibility
    parser.add_argument(
        "--unit",
        "--unit-only",
        dest="unit_only",
        action="store_true",
        help="Run only unit tests (alias: --unit)",
    )

    parser.add_argument(
        "--doc-only", action="store_true", help="Run only documentation script tests"
    )

    parser.add_argument(
        "--bdd-only", action="store_true", help="Run only BDD tests with behave"
    )

    # BDD test options
    parser.add_argument(
        "--mode",
        choices=["smoke", "hardware"],
        default="smoke",
        help="BDD test mode: smoke (safe, no hardware) or hardware (real operations)",
    )

    parser.add_argument(
        "--feature", help="Run specific BDD feature (without .feature extension)"
    )

    parser.add_argument(
        "--tag", help="Run BDD tests with specific tag (e.g., @smoke, @critical)"
    )

    # Output options
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument(
        "--format",
        choices=["pretty", "plain", "json", "junit"],
        default="pretty",
        help="BDD output format",
    )

    parser.add_argument("--output", "-o", help="Output file for BDD test results")

    # Utility options
    parser.add_argument(
        "--list-features", action="store_true", help="List available BDD test features"
    )

    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Create requirements.txt for test dependencies",
    )

    # Non-interactive/confirmation helper
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Assume yes for interactive prompts (useful for CI/automation)",
    )

    args = parser.parse_args()

    # Handle special commands
    if args.list_features:
        list_features()
        return

    if args.install_deps:
        create_requirements_file()
        return

    # Check dependencies
    if not check_dependencies():
        print("\n💡 To install test dependencies:")
        print("   pip install behave mock pre-commit")
        print("   Or run: python run_tests.py --install-deps")
        sys.exit(1)

    # Determine which tests to run
    run_integration = True
    run_unit = True
    run_doc_scripts = True
    run_bdd = True
    run_precommit = False

    if args.integration_only:
        run_unit = run_doc_scripts = run_bdd = False
    elif args.unit_only:
        run_integration = run_doc_scripts = run_bdd = False
    elif args.doc_only:
        run_integration = run_unit = run_bdd = False
    elif args.bdd_only:
        run_integration = run_unit = run_doc_scripts = False
    elif args.all:
        run_precommit = True

    # Safety warning for hardware mode
    if run_bdd and args.mode == "hardware":
        print("⚠️  " + "=" * 70)
        print("⚠️  WARNING: HARDWARE TEST MODE")
        print("⚠️  This will perform REAL dome operations!")
        print("⚠️  Ensure the dome is properly set up and safe to operate.")
        print("⚠️  " + "=" * 70)

        # Allow automation to bypass the interactive prompt with --yes/-y
        if not args.yes:
            # If we're interactive, ask the user. Otherwise abort to avoid hanging.
            if sys.stdin.isatty():
                response = (
                    input("⚠️  Continue with hardware tests? (yes/no): ")
                    .lower()
                    .strip()
                )
                if response not in ["yes", "y"]:
                    print("❌ Hardware tests cancelled")
                    sys.exit(0)
                print()
            else:
                print(
                    "❌ Non-interactive session and --yes/-y not provided. "
                    "Aborting hardware tests."
                )
                sys.exit(2)
        else:
            print("ℹ️  --yes provided: proceeding with hardware tests")
            print()

    # Run the selected test suites
    print("🔭 DOME CONTROL SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    success = True
    results = {}

    # Run integration tests
    if run_integration:
        results["integration"] = run_integration_tests()
        success = success and results["integration"]

    # Run unit tests
    if run_unit:
        results["unit"] = run_unit_tests()
        success = success and results["unit"]

    # Run doc script tests
    if run_doc_scripts:
        results["doc_scripts"] = run_doc_script_tests()
        success = success and results["doc_scripts"]

    # Run BDD tests
    if run_bdd:
        results["bdd"] = run_behave_tests(args)
        success = success and results["bdd"]

    # Run pre-commit checks
    if run_precommit:
        results["precommit"] = run_pre_commit_checks()
        success = success and results["precommit"]

    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUITE SUMMARY")
    print("=" * 80)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        test_display = {
            "integration": "Integration Tests",
            "unit": "Unit Tests",
            "doc_scripts": "Documentation Script Tests",
            "bdd": "BDD Tests",
            "precommit": "Pre-commit Checks",
        }.get(test_name, test_name)
        print(f"{test_display:.<40} {status}")

    if success:
        print("\n🎉 ALL TESTS PASSED!")
        if not run_precommit and not args.all:
            print(
                "💡 Run with --all to include pre-commit checks for complete validation"
            )
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        print("   Review the output above for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
