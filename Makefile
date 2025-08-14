# Makefile for claude-codex-bridge development

.PHONY: help install format format-check lint test coverage security clean build all check autofix

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies"
	@echo "  autofix      - Auto-fix common issues (remove unused imports, sort imports, format)"
	@echo "  format       - Format code with black"
	@echo "  format-check - Check code formatting (CI style)"
	@echo "  lint         - Run linting with flake8 and type checking with mypy"
	@echo "  test         - Run tests with pytest"
	@echo "  coverage     - Run tests with coverage report"
	@echo "  security     - Run security check with bandit"
	@echo "  check        - Run all checks (format-check, lint, test, security)"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package"
	@echo "  all          - Install, check, and build"

# Install dependencies
install:
	uv sync --group dev

# Auto-fix common issues
autofix:
	uv run autoflake --remove-all-unused-imports --in-place --recursive src/ tests/
	uv run isort src/ tests/
	uv run black src/ tests/
	@echo "Auto-fix completed!"

# Format code
format:
	uv run black src/ tests/

# Format check (CI style)
format-check:
	uv run black --check --diff src/ tests/

# Linting and type checking
lint:
	uv run mypy src/
	uv run flake8 src/ tests/

# Run tests
test:
	uv run python -m pytest tests/ -v --tb=short

# Run tests with coverage
coverage:
	uv run python -m pytest tests/ --cov=src --cov-report=xml --cov-report=term

# Security check
security:
	uv run bandit -r src/

# Run all checks (format check, lint, test, security)
check: format-check lint test security
	@echo "All checks passed!"

# Build package
build:
	uv build

# Clean build artifacts
clean:
	rm -rf dist/ build/ *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Complete workflow: install, check, and build
all: install check build
	@echo "Complete workflow finished!"
