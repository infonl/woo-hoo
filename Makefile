.PHONY: help install dev lint format typecheck test test-unit test-e2e test-cov docker-build docker-run docker-test categories generate download-samples test-real clean

# Default target
help:
	@echo "woo-hoo - LLM-powered DIWOO metadata generation"
	@echo ""
	@echo "Development:"
	@echo "  make install      Install dependencies with uv"
	@echo "  make dev          Start dev server with reload"
	@echo "  make lint         Run ruff linter"
	@echo "  make format       Format code with ruff"
	@echo "  make typecheck    Run pyrefly type checker"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run all tests"
	@echo "  make test-unit    Run unit tests only"
	@echo "  make test-e2e     Run e2e tests with httpx TestClient"
	@echo "  make test-cov     Run tests with coverage"
	@echo ""
	@echo "Real data testing (requires OPENROUTER_API_KEY):"
	@echo "  make download-samples  Download sample PDFs from open.overheid.nl"
	@echo "  make test-real         Test with real samples and OpenRouter API"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build Build Docker image"
	@echo "  make docker-run   Run in Docker"
	@echo "  make docker-test  Run tests in Docker"
	@echo ""
	@echo "CLI shortcuts:"
	@echo "  make generate FILE=doc.pdf  Generate metadata from file"
	@echo "  make categories             List Woo categories"
	@echo ""
	@echo "Other:"
	@echo "  make clean        Remove build artifacts"

# Development
install:
	uv sync --dev

dev:
	uv run uvicorn woo_hoo.main:app --host 0.0.0.0 --port 8000 --reload

lint:
	uv run ruff check src tests

format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

typecheck:
	uv run pyrefly check src

# Testing
test:
	uv run pytest tests -v

test-unit:
	uv run pytest tests/unit -v

test-e2e:
	uv run pytest tests/integration -v

test-cov:
	uv run pytest tests --cov=woo_hoo --cov-report=term-missing --cov-report=html

# Docker
docker-build:
	docker build -t woo-hoo:latest .

docker-run:
	docker run -p 8000:8000 --env-file .env woo-hoo:latest

docker-test:
	docker build --target test -t woo-hoo:test .
	docker run woo-hoo:test

# CLI shortcuts
categories:
	uv run woo-hoo categories

generate:
ifndef FILE
	$(error FILE is required. Usage: make generate FILE=path/to/document.pdf)
endif
	uv run woo-hoo generate $(FILE)

# Real data testing
download-samples:
	uv run python scripts/download_samples.py

test-real:
	uv run python scripts/test_generation.py

# Cleanup
clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
