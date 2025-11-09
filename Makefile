.PHONY: help install-hooks lint-backend lint-frontend lint format-backend format-frontend format test-backend

help:
	@echo "Available commands:"
	@echo "  make install-hooks    - Install pre-commit hooks"
	@echo "  make lint            - Run all linters (backend + frontend)"
	@echo "  make lint-backend    - Run backend linters (flake8, black --check, isort --check)"
	@echo "  make lint-frontend   - Run frontend linters (eslint, prettier --check)"
	@echo "  make format          - Format all code (backend + frontend)"
	@echo "  make format-backend  - Format backend code (black, isort)"
	@echo "  make format-frontend - Format frontend code (prettier)"
	@echo "  make test-backend    - Run backend tests"
	@echo "  make clean           - Remove cache and build files"

# Pre-commit hooks
install-hooks:
	pip install pre-commit
	pre-commit install
	@echo "✓ Pre-commit hooks installed"

# Backend linting
lint-backend:
	@echo "Running backend code checks..."
	cd backend && flake8 app/ tests/
	cd backend && black --check app/ tests/
	cd backend && isort --check-only app/ tests/
	@echo "✓ Backend code checks passed"

# Frontend linting
lint-frontend:
	@echo "Running frontend code checks..."
	cd frontend && npm run lint:check
	cd frontend && npm run format:check
	@echo "✓ Frontend code checks passed"

# All linting
lint: lint-backend lint-frontend
	@echo "✓ All code checks passed"

# Backend formatting
format-backend:
	@echo "Formatting backend code..."
	cd backend && black app/ tests/
	cd backend && isort app/ tests/
	@echo "✓ Backend code formatted"

# Frontend formatting
format-frontend:
	@echo "Formatting frontend code..."
	cd frontend && npm run format
	cd frontend && npm run lint
	@echo "✓ Frontend code formatted"

# All formatting
format: format-backend format-frontend
	@echo "✓ All code formatted"

# Testing
test-backend:
	@echo "Running backend tests..."
	cd backend && pytest
	@echo "✓ Backend tests passed"

# Clean
clean:
	@echo "Cleaning cache and build files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/htmlcov 2>/dev/null || true
	rm -rf frontend/dist 2>/dev/null || true
	rm -rf frontend/node_modules/.cache 2>/dev/null || true
	@echo "✓ Cleaned"
