#!/usr/bin/env python3
"""
Dome Control System Test Runner.

This script provides an easy way to run the BDD test suite for the dome control
system. It supports both smoke test mode (safe, no hardware) and hardware test
mode (real operations).

Usage:
    python run_tests.py                    # Run smoke tests (default)
    python run_tests.py --mode smoke       # Run smoke tests explicitly
    python run_tests.py --mode hardware    # Run hardware tests (CAUTION!)
    python run_tests.py --feature rotation # Run specific feature
    python run_tests.py --tag @critical    # Run tests with specific tag
    python run_tests.py --help             # Show help
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []

    try:
        import behave
    except ImportError:
        missing_deps.append("behave")

    # Check if dome modules are available
    script_dir = Path(__file__).parent
    parent_dir = script_dir.parent
    sys.path.insert(0, str(parent_dir))

    try:
        from config import load_config
        from dome import Dome
    except ImportError as e:
        print(f"❌ Error importing dome modules: {e}")
        print("   Make sure you're running from the correct directory")
        return False

    if missing_deps:
        print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
        print("   Install with: pip install behave")
        return False

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
        description="Dome Control System BDD Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                     # Run all smoke tests
  python run_tests.py --mode hardware     # Run hardware tests (CAUTION!)
  python run_tests.py --feature rotation  # Run rotation tests only
  python run_tests.py --tag @smoke        # Run smoke-tagged tests
  python run_tests.py --list-features     # List available features

Test Modes:
  smoke    - Safe mode with no real hardware operations (default)
  hardware - Real hardware mode with actual dome movements (CAUTION!)

Notes:
  - Hardware mode requires proper dome setup and safety precautions
  - Smoke mode is safe for development and continuous integration
  - Features are automatically run in both modes unless tagged otherwise
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["smoke", "hardware"],
        default="smoke",
        help="Test mode: smoke (safe, no hardware) or hardware (real operations)",
    )

    parser.add_argument(
        "--feature", help="Run specific feature (without .feature extension)"
    )

    parser.add_argument(
        "--tag", help="Run tests with specific tag (e.g., @smoke, @critical)"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument(
        "--format",
        choices=["pretty", "plain", "json", "junit"],
        default="pretty",
        help="Output format",
    )

    parser.add_argument("--output", "-o", help="Output file for test results")

    parser.add_argument(
        "--list-features", action="store_true", help="List available test features"
    )

    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Create requirements.txt for test dependencies",
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
        print("   pip install behave mock")
        print("   Or run: python run_tests.py --install-deps")
        sys.exit(1)

    # Safety warning for hardware mode
    if args.mode == "hardware":
        print("⚠️  " + "=" * 70)
        print("⚠️  WARNING: HARDWARE TEST MODE")
        print("⚠️  This will perform REAL dome operations!")
        print("⚠️  Ensure the dome is properly set up and safe to operate.")
        print("⚠️  " + "=" * 70)

        response = input("⚠️  Continue with hardware tests? (yes/no): ").lower().strip()
        if response not in ["yes", "y"]:
            print("❌ Hardware tests cancelled")
            sys.exit(0)
        print()

    # Run tests
    success = run_behave_tests(args)

    if success:
        print("\n✅ All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed or encountered errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
