#!/bin/bash
# Virtual Environment Setup Script for INDI Dome Driver
# This script creates and configures a Python virtual environment with all required dependencies

set -e  # Exit on any error

VENV_DIR="venv"
PYTHON_CMD="python3"

echo "🔧 Setting up INDI Dome Driver development environment..."

# Check if Python 3 is available
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Error: Python 3 is required but not found in PATH"
    echo "Please install Python 3.7 or later"
    exit 1
fi

# Display Python version
echo "📋 Using Python version: $($PYTHON_CMD --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "🏗️  Creating virtual environment in $VENV_DIR..."
    $PYTHON_CMD -m venv $VENV_DIR
else
    echo "✅ Virtual environment already exists in $VENV_DIR"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source $VENV_DIR/bin/activate

# Upgrade pip to latest version
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install production dependencies
echo "📦 Installing production dependencies..."
pip install -r requirements.txt

# Install development dependencies if available
if [ -f "requirements-dev.txt" ]; then
    echo "🛠️  Installing development dependencies..."
    pip install -r requirements-dev.txt
fi

# Install test dependencies
if [ -f "test/requirements.txt" ]; then
    echo "🧪 Installing test dependencies..."
    pip install -r test/requirements.txt
fi

# Install pre-commit hooks if available
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🪝 Installing pre-commit hooks..."
    pre-commit install
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To deactivate the virtual environment, run:"
echo "  deactivate"
echo ""
echo "To run tests:"
echo "  python test/run_tests.py"
echo ""
echo "To run linting:"
echo "  flake8 ."
echo "  black --check ."
echo ""
echo "Happy coding! 🚀"
