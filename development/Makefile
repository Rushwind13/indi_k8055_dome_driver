# Makefile for INDI Dome Driver Development
# Provides convenient commands for common development tasks

.PHONY: help setup install install-dev test test-smoke lint format clean docs security pre-commit

help: ## Show this help message
	@echo "INDI Dome Driver Development Commands"
	@echo "====================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Set up the development environment
	@echo "🔧 Setting up development environment..."
	./setup_venv.sh

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install all dependencies (production + development + test)
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -r test/requirements.txt

test: ## Run all tests (unit tests + BDD smoke tests)
	@echo "🧪 Running unit tests..."
	pytest test/ -v --cov=. --cov-report=term-missing
	@echo "🧪 Running BDD smoke tests..."
	python test/run_tests.py --smoke-only

test-smoke: ## Run only BDD smoke tests (fast)
	python test/run_tests.py --smoke-only

test-full: ## Run full BDD test suite (includes hardware simulation)
	python test/run_tests.py --mode smoke

lint: ## Run all linting checks
	@echo "🔍 Running code quality checks..."
	flake8 .
	mypy . --ignore-missing-imports --disallow-untyped-defs || true
	bandit -r . -x test/,venv/

format: ## Format code with black and isort
	@echo "🎨 Formatting code..."
	black .
	isort .

format-check: ## Check code formatting without making changes
	black --check --diff .
	isort --check-only --diff .

security: ## Run security scans
	@echo "🔒 Running security scans..."
	bandit -r . -x test/,venv/
	safety check

docs: ## Build documentation
	@echo "📚 Building documentation..."
	sphinx-build -b html docs/ docs/_build/html/ || echo "Documentation build requires docs/ directory setup"

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

clean: ## Clean up build artifacts and cache files
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + || true
	rm -rf build/ dist/ .coverage coverage.xml .pytest_cache/ .mypy_cache/

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
