# Makefile for INDI Dome Driver Development
# Provides convenient commands for common development tasks

.PHONY: help setup install install-dev test test-smoke lint format clean docs security pre-commit

help: ## Show this help message
	@echo "INDI Dome Driver Development Commands"
	@echo "====================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## 🐌 Set up the development environment
	@python -m venv venv
	@echo "Virtual environment created. Now run: source venv/bin/activate && make install-dev"

install: ## Install production dependencies

install-dev: ## 🐌 Install all dependencies (production + development + test)
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test: ## Run all tests (integration, unit, doc, and BDD smoke tests)
	@echo "🧪 Running comprehensive test suite..."
	python test/run_tests.py

test-smoke: ## 🏎️ Run only BDD smoke tests (fast)
	@echo "🧪 Running BDD smoke tests only..."
	python test/run_tests.py --bdd-only --mode smoke

test-unit: ## Run unit tests with verbose output and coverage report
	@echo "🧪 Running unit tests with coverage..."
	pytest test/unit/ -v --cov=indi_driver/lib --cov-report=term-missing --cov-report=html
	@echo "📊 Coverage report generated in htmlcov/ directory"

test-integration: ## Run integration tests with coverage analysis
	@echo "🧪 Running integration tests with coverage..."
	@echo "ℹ️  Note: Scripts are tested functionally but coverage focuses on library code"
	coverage run --source=indi_driver/lib -m pytest test/integration/ -v
	@echo ""
	@echo "📊 Integration Test Coverage Report (Library Only):"
	coverage report --show-missing
	@echo ""
	@echo "📁 Detailed HTML coverage report: htmlcov/index.html"
	coverage html

test-bdd: ## Run BDD tests with coverage analysis
	@echo "🧪 Running BDD tests with coverage..."
	@echo "ℹ️  Note: Behavior-driven tests exercise user stories and scenarios"
	DOME_TEST_MODE=smoke coverage run --source=indi_driver/lib -m behave test/integration/features --tags=~@manual --no-capture --summary
	@echo ""
	@echo "📊 BDD Test Coverage Report (Library Only):"
	coverage report --show-missing
	@echo ""
	@echo "📁 Detailed HTML coverage report: htmlcov/index.html"
	coverage html

coverage-combined: ## 🐌 Run all tests and combine coverage data
	@echo "🧪 Running comprehensive coverage analysis..."
	@echo "ℹ️  Combining unit, integration, and BDD test coverage"
	@echo ""
	@echo "🔹 Running unit tests with coverage..."
	coverage run --source=indi_driver/lib -m pytest test/unit/ -v
	@echo ""
	@echo "🔹 Running integration tests with coverage (appending)..."
	coverage run --append --source=indi_driver/lib -m pytest test/integration/ -v
	@echo ""
	@echo "🔹 Running BDD tests with coverage (appending)..."
	DOME_TEST_MODE=smoke coverage run --append --source=indi_driver/lib -m behave test/integration/features --tags=~@manual --no-capture --summary
	@echo ""
	@echo "📊 COMBINED COVERAGE REPORT (All Test Sources):"
	@echo "================================================"
	coverage report --show-missing
	@echo ""
	@echo "📁 Combined HTML coverage report: htmlcov/index.html"
	coverage html
	@echo ""
	@echo "✨ Coverage analysis complete! Check htmlcov/index.html for detailed breakdown."

coverage-gather: ## 🐌 Gather coverage data from all test sources (without analysis)
	@echo "📊 Gathering coverage data from all test sources..."
	@echo "ℹ️  Running tests and collecting coverage data only"
	@echo ""
	@echo "🔹 Running unit tests with coverage..."
	coverage run --source=indi_driver/lib -m pytest test/unit/ -v
	@echo ""
	@echo "🔹 Running integration tests with coverage (appending)..."
	coverage run --append --source=indi_driver/lib -m pytest test/integration/ -v
	@echo ""
	@echo "🔹 Running BDD tests with coverage (appending)..."
	DOME_TEST_MODE=smoke coverage run --append --source=indi_driver/lib -m behave test/integration/features --tags=~@manual --no-capture --summary
	@echo ""
	@echo "✅ Coverage data gathering complete! Use 'make coverage-analyze' to view results."

coverage-analyze: ## 🏎️ Analyze previously gathered coverage data
	@echo "📊 COMBINED COVERAGE ANALYSIS:"
	@echo "================================================"
	@echo "ℹ️  Analyzing coverage data from all test sources"
	@echo ""
	coverage report --show-missing
	@echo ""
	@echo "📁 Generating detailed HTML coverage report..."
	coverage html
	@echo "✨ HTML report available at: htmlcov/index.html"
	@echo ""
	@echo "💡 Use 'make coverage-gather' to refresh data or 'make test-coverage-combined' for full workflow"

test-full: ## 🐌 Run all tests including pre-commit checks and detailed coverage
	@echo "🧪 Running full test suite with all validations..."
	python test/run_tests.py --all
	@echo "🧪 Running detailed unit test coverage..."
	pytest test/unit/ -v --cov=indi_driver/lib --cov-report=term-missing --cov-report=html
	@echo "🧪 Running integration test coverage (library focus)..."
	coverage run --source=indi_driver/lib -m pytest test/integration/ -v
	coverage report --show-missing
	coverage html -d htmlcov_integration
	@echo "📊 Coverage reports: htmlcov/ (unit) and htmlcov_integration/ (integration)"

test-calibrate: ## 🎯 Run calibration data capture tests (hardware mode only)
	@echo "📊 Running calibration data capture tests..."
	@echo "⚠️  WARNING: This target only works in HARDWARE mode!"
	@echo "ℹ️  Set DOME_TEST_MODE=hardware to capture real calibration data"
	@if [ "$(DOME_TEST_MODE)" != "hardware" ]; then \
		echo "❌ Calibration tests require DOME_TEST_MODE=hardware"; \
		echo "💡 Usage: DOME_TEST_MODE=hardware make test-calibrate"; \
		exit 1; \
	fi
	@echo "🔧 Running calibration-specific INDI script tests..."
	python -m pytest test/integration/test_indi_scripts.py::TestINDIScripts::test_calibration_position_accuracy -v
	python -m pytest test/integration/test_indi_scripts.py::TestINDIScripts::test_calibration_home_repeatability -v
	python -m pytest test/integration/test_indi_scripts.py::TestINDIScripts::test_calibration_rotation_timing -v
	@echo "🔧 Running calibration-enhanced BDD rotation tests..."
	python test/run_tests.py --feature dome_rotation --mode hardware --yes
	@echo "📋 Calibration data capture complete!"
	@echo "💡 Check test output above for calibration statistics and recommendations"

test-hardware-startup: ## 🚀 Run hardware startup sequence tests (safe, short movements)
	@echo "🚀 Running hardware startup sequence tests..."
	@echo "⚠️  WARNING: This will control real dome hardware!"
	@echo "ℹ️  Performing safe startup validation with short movements (<5 seconds)"
	@if [ "$(DOME_TEST_MODE)" != "hardware" ]; then \
		echo "🔧 Setting DOME_TEST_MODE=hardware for startup tests"; \
		export DOME_TEST_MODE=hardware; \
	fi
	@echo "🌧️  Rain safety: WEATHER_RAINING=$(WEATHER_RAINING)"
	@echo "🔍 Phase 1: Hardware connectivity validation..."
	python test/run_tests.py --hardware-startup --yes
	@echo "✅ Hardware startup sequence complete!"
	@echo "💡 System ready for extended hardware integration testing"

test-hardware-sequence: ## 🔄 Run full hardware test sequence with proper ordering
	@echo "🔄 Running full hardware test sequence..."
	@echo "⚠️  WARNING: This will perform extensive dome movements!"
	@echo "ℹ️  Tests will run in dependency-ordered sequence for safety"
	@if [ "$(DOME_TEST_MODE)" != "hardware" ]; then \
		echo "❌ Hardware sequence tests require DOME_TEST_MODE=hardware"; \
		echo "💡 Usage: DOME_TEST_MODE=hardware make test-hardware-sequence"; \
		exit 1; \
	fi
	@echo "🔍 Pre-flight hardware validation..."
	$(MAKE) test-hardware-startup DOME_TEST_MODE=hardware
	@echo "🔧 Running sequenced integration tests..."
	DOME_TEST_MODE=hardware python test/run_tests.py --integration-only --yes
	@echo "📊 Running calibration data capture..."
	$(MAKE) test-calibrate DOME_TEST_MODE=hardware
	@echo "✅ Full hardware test sequence complete!"
	@echo "🎉 System validated for production hardware integration!"

test-hardware-safe: ## 🛡️ Run minimal hardware tests for initial validation
	@echo "🛡️  Running minimal hardware validation tests..."
	@echo "ℹ️  Safe tests: connectivity + short movements only"
	@echo "⏱️  Expected duration: <2 minutes"
	@if [ "$(DOME_TEST_MODE)" != "hardware" ]; then \
		echo "🔧 Setting DOME_TEST_MODE=hardware for safe tests"; \
		export DOME_TEST_MODE=hardware; \
	fi
	@echo "🌧️  Rain safety check enabled"
	@echo "🔍 Running hardware startup sequence..."
	python test/run_tests.py --hardware-startup --yes
	@echo "🔧 Running basic safety system tests..."
	DOME_TEST_MODE=hardware python -m pytest test/integration/test_safety_systems.py::TestSafetySystems::test_emergency_stop_response_time -v
	@echo "✅ Minimal hardware validation complete!"
	@echo "💡 Ready for extended testing with 'make test-hardware-sequence'"

lint: ## Run all linting checks
	@echo "🔍 Running code quality checks..."
	flake8 .
	mypy . --ignore-missing-imports --disallow-untyped-defs || true
	bandit -r . -x test/,venv/

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	black .
	isort .

format-check: ## 🏎️ Check code formatting without making changes
	black --check --diff indi_driver/ test/
	isort --check-only --diff indi_driver/ test/

security: ## Run security scans
	@echo "🔒 Running security scans..."
	bandit -r . -x test/,venv/
	safety check

docs: ## Build documentation
	@echo "📚 Building documentation..."
	sphinx-build -b html docs/ docs/_build/html/ || echo "Documentation build requires docs/ directory setup"

pre-commit: ## 🐌 Run pre-commit hooks on all files
	pre-commit run --all-files

clean: ## 🏎️ Clean up build artifacts and cache files
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + || true
	rm -rf build/ dist/ .coverage coverage.xml .pytest_cache/ .mypy_cache/

check-k8055: ## 🔌 Check if libk8055 library is available
	@echo "🔌 Checking libk8055 availability..."
	@python3 -c "import pyk8055; print('✅ libk8055 available')" || (echo "❌ libk8055 not available - install libk8055 and pyk8055 bindings" && exit 1)

hardware-test-connect: ## 🔌 Test hardware connection via connect script
	@python3 hardware_test_helper.py connect

hardware-test-status: ## 📊 Test status script output format
	@python3 hardware_test_helper.py status

hardware-sysinfo: ## 📋 Create system information snapshot
	@python3 hardware_test_helper.py sysinfo

hardware-indi-config: ## ⚙️ Setup INDI driver configuration
	@python3 hardware_test_helper.py indi-config

hardware-test-all: ## 🧪 Run all hardware integration helper tests
	@python3 hardware_test_helper.py all

venv: ## Create virtual environment (if not exists)
	python3 -m venv venv
	@echo "Virtual environment created. Activate with: source venv/bin/activate"

activate: ## Show command to activate virtual environment
	@echo "To activate the virtual environment, run:"
	@echo "  source venv/bin/activate"

# Development workflow commands
dev-setup: setup install-dev pre-commit ## Complete development setup
	@echo "✅ Development environment ready!"
	@echo "To get started:"
	@echo "  1. source venv/bin/activate"
	@echo "  2. make test"
	@echo "  3. Start developing!"

dev-test: format-check lint test ## Run all development checks (formatting, linting, tests)

ci: dev-test ## Run the same checks as CI (useful before pushing)
	@echo "✅ All CI checks passed locally!"

# Release preparation
release-check: clean dev-test security docs ## Run all checks before release
	@echo "✅ Release checks completed!"

# Python 2.7 validation targets
test-py27: ## 🐍 Run Python 2.7 validation tests
	@echo "🐍 Running Python 2.7 validation..."
	@if [ ! -d "venv_py27" ]; then \
		echo "❌ Python 2.7 virtual environment not found"; \
		echo "💡 Run 'make setup-py27' to create it"; \
		exit 1; \
	fi
	source venv_py27/bin/activate && python test/python2/validate_py27.py

test-py27-verbose: ## 🐍 Run Python 2.7 validation with verbose output
	@echo "🐍 Running Python 2.7 validation (verbose)..."
	source venv_py27/bin/activate && python test/python2/validate_py27.py --verbose

test-py27-persistence: ## 🐍 Run Python 2.7 persistence tests only
	@echo "🐍 Running Python 2.7 persistence tests..."
	source venv_py27/bin/activate && python test/python2/validate_py27.py --persistence-only

test-py27-full: ## 🐍 Run complete Python 2.7 validation with linting
	@echo "🐍 Running complete Python 2.7 validation..."
	@if [ -f "test/python2/run_precommit_py27.sh" ]; then \
		echo "🔍 Running Python 2.7 linting..."; \
		./test/python2/run_precommit_py27.sh; \
	fi
	$(MAKE) test-py27-verbose

setup-py27: ## 🐍 Set up Python 2.7 virtual environment
	@echo "🐍 Setting up Python 2.7 virtual environment..."
	@if command -v python2.7 >/dev/null 2>&1; then \
		python2.7 -m virtualenv venv_py27; \
		echo "✅ Python 2.7 environment created"; \
		echo "💡 Activate with: source venv_py27/bin/activate"; \
	else \
		echo "❌ Python 2.7 not found on system"; \
		echo "💡 Install Python 2.7 first"; \
		exit 1; \
	fi

py27-validation: ## 🐍 Complete Python 2.7 validation workflow
	@echo "🐍 Running complete Python 2.7 validation workflow..."
	$(MAKE) test-py27-full
	@echo "✅ Python 2.7 validation complete!"
	@echo "🚀 Ready for deployment to Python 2.7 environments"
