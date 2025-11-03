#!/usr/bin/env python3
"""
Hardware Integration Test Helper Script
Provides common test operations for hardware integration testing.
"""

import json
import platform
import subprocess
import sys
import unittest
from pathlib import Path

# Add the project lib directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "indi_driver" / "lib"))
sys.path.insert(0, str(project_root / "test" / "integration"))


def test_connect_script():
    """Test the connect script directly and report results."""
    print("🔌 Testing hardware connection via connect script...")

    scripts_dir = project_root / "indi_driver" / "scripts"
    connect_script = scripts_dir / "connect.py"

    if not connect_script.exists():
        print(f"❌ Connect script not found: {connect_script}")
        return False

    try:
        result = subprocess.run(
            ["python3", str(connect_script)], capture_output=True, text=True, timeout=30
        )

        print(f"Connect exit code: {result.returncode}")
        if result.returncode == 0:
            print("✅ Hardware connection successful")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print("❌ Hardware connection failed")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Connect script timed out")
        return False
    except Exception as e:
        print(f"❌ Error running connect script: {e}")
        return False


def test_status_format():
    """Test status script output format validation."""
    print("📊 Testing status script output format...")

    try:
        # Create test instance
        suite = unittest.TestLoader().loadTestsFromName(
            "test_indi_scripts.TestINDIScripts.test_status_script_output_format"
        )
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)

        if result.wasSuccessful():
            print("✅ Status format validation passed")
            return True
        else:
            print("❌ Status format validation failed")
            for failure in result.failures + result.errors:
                print(f"Error: {failure[1]}")
            return False

    except ImportError as e:
        print(f"❌ Could not import test module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error running status format test: {e}")
        return False


def create_system_info():
    """Create system information snapshot for documentation."""
    print("📋 Creating system information snapshot...")

    try:
        # Get git commit hash
        try:
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=project_root, text=True
            ).strip()
        except subprocess.CalledProcessError:
            git_commit = "Not available (not a git repository)"

        info = {
            "date": subprocess.check_output(["date"], text=True).strip(),
            "system": platform.system(),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "hostname": platform.node(),
            "git_commit": git_commit,
            "project_root": str(project_root),
        }

        output_file = project_root / "hardware_integration_info.json"
        with open(output_file, "w") as f:
            json.dump(info, f, indent=2)

        print(f"✅ System information saved to {output_file}")
        print(f"System: {info['system']} {info['platform']}")
        print(f"Python: {info['python_version']}")
        print(f"Hostname: {info['hostname']}")
        print(f"Git commit: {git_commit[:8]}...")
        return True

    except Exception as e:
        print(f"❌ Error creating system info: {e}")
        return False


def setup_indi_config():
    """Setup INDI driver configuration file."""
    print("⚙️  Setting up INDI driver configuration...")

    try:
        # Create ~/.indi directory if it doesn't exist
        indi_dir = Path.home() / ".indi"
        indi_dir.mkdir(exist_ok=True)

        # Copy our config file to the INDI directory
        source_config = project_root / "indi_driver" / "dome_script_config.xml"
        target_config = indi_dir / "dome_script_config.xml"

        if not source_config.exists():
            print(f"❌ Source config file not found: {source_config}")
            return False

        # Read and update the config with current project path
        with open(source_config, "r") as f:
            config_content = f.read()

        # Replace placeholder path with actual project path
        scripts_path = str(project_root / "indi_driver" / "scripts")
        config_content = config_content.replace(
            "/home/pi/indi_k8055_dome_driver/indi_driver/scripts", scripts_path
        )

        with open(target_config, "w") as f:
            f.write(config_content)

        print(f"✅ INDI configuration created: {target_config}")
        print(f"Scripts folder: {scripts_path}")
        return True

    except Exception as e:
        print(f"❌ Error setting up INDI config: {e}")
        return False


def main():
    """Main function to run all operations based on command line arguments."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 hardware_test_helper.py connect      # Test connect script")
        print("  python3 hardware_test_helper.py status       # Test status format")
        print("  python3 hardware_test_helper.py sysinfo      # Create system info")
        print("  python3 hardware_test_helper.py indi-config  # Setup INDI config")
        print("  python3 hardware_test_helper.py all          # Run all tests")
        sys.exit(1)

    command = sys.argv[1].lower()
    success = True

    if command == "connect":
        success = test_connect_script()
    elif command == "status":
        success = test_status_format()
    elif command == "sysinfo":
        success = create_system_info()
    elif command == "indi-config":
        success = setup_indi_config()
    elif command == "all":
        print("🧪 Running all hardware integration tests...")
        success = (
            test_connect_script()
            and test_status_format()
            and create_system_info()
            and setup_indi_config()
        )
        if success:
            print("✅ All hardware integration tests completed successfully")
        else:
            print("❌ Some hardware integration tests failed")
    else:
        print(f"❌ Unknown command: {command}")
        success = False

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
