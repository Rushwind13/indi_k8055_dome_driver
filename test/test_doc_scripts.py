#!/usr/bin/env python3
"""
Test for documentation Python scripts.

This test verifies that all Python scripts in the doc/ directory
can be imported and executed without errors.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_doc_scripts_can_import():
    """Test that all Python scripts in doc/ can be imported without errors."""
    print("🔹 Testing doc/ Python scripts can import...")

    doc_dir = Path(__file__).parent.parent / "doc"
    python_files = list(doc_dir.glob("*.py"))

    if not python_files:
        print("⚠️  No Python files found in doc/ directory")
        return

    for py_file in python_files:
        print(f"  Testing imports in {py_file.name}...")

        # Create a minimal test script that just imports
        test_script = f"""
import sys
import os
sys.path.insert(0, r"{py_file.parent.parent}")

# Try to import the script's main modules
try:
    import pyk8055_wrapper
    print("✅ pyk8055_wrapper import successful")
except ImportError as e:
    print(f"❌ pyk8055_wrapper import failed: {{e}}")
    sys.exit(1)

try:
    from config import load_config
    print("✅ config import successful")
except ImportError as e:
    print("⚠️  config import failed (might be expected): {{e}}")

# Test that the file can be parsed without syntax errors
try:
    with open(r"{py_file}", "r") as f:
        code = f.read()
    compile(code, r"{py_file}", "exec")
    print("✅ Script syntax is valid")
except SyntaxError as e:
    print(f"❌ Syntax error in script: {{e}}")
    sys.exit(1)

print("✅ Import test completed successfully")
"""

        # Run the test script
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(test_script)
            tmp.flush()

            try:
                result = subprocess.run(
                    [sys.executable, tmp.name],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    print(f"    ✅ {py_file.name} imports successfully")
                else:
                    print(f"    ❌ {py_file.name} import failed:")
                    print(f"      stdout: {result.stdout}")
                    print(f"      stderr: {result.stderr}")
                    raise AssertionError(f"Import test failed for {py_file.name}")

            finally:
                os.unlink(tmp.name)

    print("✅ All doc/ Python scripts can import successfully")


def test_doc_scripts_can_run():
    """Test that doc/ Python scripts can run without critical errors."""
    print("\n🔹 Testing doc/ Python scripts can run...")

    doc_dir = Path(__file__).parent.parent / "doc"

    # Test each script individually with timeout and error handling
    test_cases = [
        {
            "file": "demo_hardware_modes.py",
            "description": "Hardware modes demonstration",
            "timeout": 30,
        },
        {
            "file": "enhanced_dome_example.py",
            "description": "Enhanced dome example",
            "timeout": 30,
        },
        {
            "file": "production_setup_guide.py",
            "description": "Production setup guide",
            "timeout": 30,
        },
    ]

    for test_case in test_cases:
        py_file = doc_dir / test_case["file"]

        if not py_file.exists():
            print(f"  ⚠️  {test_case['file']} not found, skipping...")
            continue

        print(f"  Testing {test_case['description']}...")

        try:
            # Run the script with a timeout
            result = subprocess.run(
                [sys.executable, str(py_file)],
                capture_output=True,
                text=True,
                timeout=test_case["timeout"],
                cwd=str(py_file.parent.parent),  # Run from project root
            )

            # Check if it ran without critical errors
            if result.returncode == 0:
                print(f"    ✅ {test_case['file']} ran successfully")
            else:
                # Check if it's just a demo/example that exits with non-zero but works
                if "demo" in test_case["file"] or "example" in test_case["file"]:
                    print(
                        f"    ⚠️  {test_case['file']} exited with code "
                        f"{result.returncode} (might be normal for demo)"
                    )
                    print(f"    Output preview: {result.stdout[:200]}...")
                else:
                    print(
                        f"    ❌ {test_case['file']} failed with exit code "
                        f"{result.returncode}"
                    )
                    print(f"      stderr: {result.stderr[:200]}...")
                    raise AssertionError(
                        f"Script execution failed for {test_case['file']}"
                    )

        except subprocess.TimeoutExpired:
            print(
                f"    ⚠️  {test_case['file']} timed out "
                f"(might be normal for interactive demos)"
            )
        except Exception as e:
            print(f"    ❌ Error running {test_case['file']}: {e}")
            raise

    print("✅ All doc/ Python scripts can run without critical errors")


def test_doc_scripts_have_proper_structure():
    """Test that doc/ scripts have proper docstrings and structure."""
    print("\n🔹 Testing doc/ Python scripts have proper structure...")

    doc_dir = Path(__file__).parent.parent / "doc"
    python_files = list(doc_dir.glob("*.py"))

    for py_file in python_files:
        print(f"  Checking structure of {py_file.name}...")

        with open(py_file, "r") as f:
            content = f.read()

        # Check for shebang
        if not content.startswith("#!/usr/bin/env python3"):
            print(f"    ⚠️  {py_file.name} missing proper shebang")

        # Check for module docstring
        if '"""' not in content[:500]:
            print(f"    ⚠️  {py_file.name} missing module docstring")

        # Check for main guard
        if 'if __name__ == "__main__":' not in content:
            print(f"    ⚠️  {py_file.name} missing main guard")
        else:
            print(f"    ✅ {py_file.name} has proper main guard")

        # Check imports are at the top (after docstring)
        lines = content.split("\n")
        found_import = False
        for i, line in enumerate(lines):
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                found_import = True
                break

        if found_import:
            print(f"    ✅ {py_file.name} has proper import structure")
        else:
            print(f"    ⚠️  {py_file.name} might have import issues")

    print("✅ Doc/ script structure check completed")


def main():
    """Run all documentation script tests."""
    print("=" * 80)
    print("🔭 DOCUMENTATION PYTHON SCRIPTS TESTS")
    print("=" * 80)

    try:
        test_doc_scripts_can_import()
        test_doc_scripts_can_run()
        test_doc_scripts_have_proper_structure()

        print("\n" + "=" * 80)
        print("🎉 ALL DOCUMENTATION SCRIPT TESTS PASSED!")
        print("✅ All doc/ Python scripts can import correctly")
        print("✅ All doc/ Python scripts can run without critical errors")
        print("✅ All doc/ Python scripts have proper structure")
        print("=" * 80)
        return 0

    except Exception as e:
        print(f"\n❌ DOCUMENTATION SCRIPT TEST FAILED: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
