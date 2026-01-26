.PHONY: help install dev lint format typecheck test test-unit test-e2e test-cov docker-build docker-run docker-test categories generate download-samples test-real clean

# Sentinel file to track if dependencies are installed
INSTALL_SENTINEL := .install-sentinel

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
	@echo "  make download-samples       Download sample PDFs from open.overheid.nl"
	@echo "  make test-real              Test all samples (XML mode - default)"
	@echo "  make test-real-json         Test all samples (JSON mode)"
	@echo "  make test-real-single       Test single PDF (default: woo_besluit)"
	@echo "  make test-real-single-json  Test single PDF in JSON mode"
	@echo "  make test-real-single FILE=path/to/doc.pdf"
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
install: $(INSTALL_SENTINEL)

$(INSTALL_SENTINEL): pyproject.toml uv.lock
	uv sync --extra dev
	@touch $(INSTALL_SENTINEL)

dev: $(INSTALL_SENTINEL)
	uv run uvicorn woo_hoo.main:app --host 0.0.0.0 --port 8000 --reload

lint: $(INSTALL_SENTINEL)
	uv run ruff check src tests

format: $(INSTALL_SENTINEL)
	uv run ruff format src tests
	uv run ruff check --fix src tests

typecheck: $(INSTALL_SENTINEL)
	uv run pyrefly check src

# Testing
test: $(INSTALL_SENTINEL)
	uv run pytest tests -v

test-unit: $(INSTALL_SENTINEL)
	uv run pytest tests/unit -v

test-e2e: $(INSTALL_SENTINEL)
	uv run pytest tests/integration -v

test-cov: $(INSTALL_SENTINEL)
	uv run pytest tests --cov=woo_hoo --cov-report=term-missing --cov-report=html

# Docker
docker-build:
	docker build -t woo-hoo:latest .

docker-run: docker-build
	docker run -p 8000:8000 --env-file .env woo-hoo:latest

docker-test: docker-build
	docker build --target test -t woo-hoo:test .
	docker run woo-hoo:test

# CLI shortcuts
categories: $(INSTALL_SENTINEL)
	uv run woo-hoo categories

generate: $(INSTALL_SENTINEL)
ifndef FILE
	$(error FILE is required. Usage: make generate FILE=path/to/document.pdf)
endif
	uv run woo-hoo generate $(FILE)

# Real data testing (requires OPENROUTER_API_KEY)
# Default mode is XML (LLM outputs XML, transformed to JSON in code)
download-samples: $(INSTALL_SENTINEL)
	uv run python scripts/download_samples.py

test-real: $(INSTALL_SENTINEL)
	uv run python scripts/test_e2e.py --all

test-real-verbose: $(INSTALL_SENTINEL)
	uv run python scripts/test_e2e.py --all --verbose

# JSON mode (direct JSON output from LLM)
test-real-json: $(INSTALL_SENTINEL)
	uv run python scripts/test_e2e.py --all --json

test-real-json-verbose: $(INSTALL_SENTINEL)
	uv run python scripts/test_e2e.py --all --json --verbose

# Test single file: make test-real-single or make test-real-single FILE=path/to/doc.pdf
test-real-single: $(INSTALL_SENTINEL)
ifdef FILE
	uv run python scripts/test_e2e.py --file $(FILE) --verbose
else
	uv run python scripts/test_e2e.py --file data/samples/woo_besluit_landsadvocaat_stikstof.pdf --verbose
endif

test-real-single-json: $(INSTALL_SENTINEL)
ifdef FILE
	uv run python scripts/test_e2e.py --file $(FILE) --verbose --json
else
	uv run python scripts/test_e2e.py --file data/samples/woo_besluit_landsadvocaat_stikstof.pdf --verbose --json
endif

show-prompt: $(INSTALL_SENTINEL)
	uv run python scripts/test_e2e.py --show-prompt

# Cleanup
clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info $(INSTALL_SENTINEL)
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
