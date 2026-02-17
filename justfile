# woo-hoo - LLM-powered DIWOO metadata generation

# Show available recipes
default:
    @just --list

# Install dependencies with uv
install:
    uv sync --extra dev

# Start dev server with reload
dev: install
    uv run uvicorn woo_hoo.main:app --host 0.0.0.0 --port 8000 --reload

# Run ruff linter
lint: install
    uv run ruff check src tests

# Format code with ruff
format: install
    uv run ruff format src tests
    uv run ruff check --fix src tests

# Run pyrefly type checker
typecheck: install
    uv run pyrefly check src

# Run all tests
test: install
    uv run pytest tests -v

# Run unit tests only
test-unit: install
    uv run pytest tests/unit -v

# Run e2e tests with httpx TestClient
test-e2e: install
    uv run pytest tests/integration -v

# Run tests with coverage
test-cov: install
    uv run pytest tests --cov=woo_hoo --cov-report=term-missing --cov-report=html

# Build Docker image
docker-build:
    docker build -t woo-hoo:latest .

# Run in Docker
docker-run: docker-build
    docker run -p 8000:8000 --env-file .env woo-hoo:latest

# Run tests in Docker
docker-test: docker-build
    docker build --target test -t woo-hoo:test .
    docker run woo-hoo:test

# List Woo categories
categories: install
    uv run woo-hoo categories

# Generate metadata from file
generate FILE: install
    uv run woo-hoo generate {{ FILE }}

# Download sample PDFs from open.overheid.nl
download-samples: install
    uv run python scripts/download_samples.py

# Test all samples (XML mode - default)
test-real: install
    uv run python scripts/test_e2e.py --all

# Test all samples verbose
test-real-verbose: install
    uv run python scripts/test_e2e.py --all --verbose

# Test all samples JSON mode
test-real-json: install
    uv run python scripts/test_e2e.py --all --json

# Test all samples JSON verbose
test-real-json-verbose: install
    uv run python scripts/test_e2e.py --all --json --verbose

# Test single file (default: woo_besluit sample)
test-real-single FILE="data/samples/woo_besluit_landsadvocaat_stikstof.pdf": install
    uv run python scripts/test_e2e.py --file {{ FILE }} --verbose

# Test single file JSON mode
test-real-single-json FILE="data/samples/woo_besluit_landsadvocaat_stikstof.pdf": install
    uv run python scripts/test_e2e.py --file {{ FILE }} --verbose --json

# Show the system prompt sent to the LLM
show-prompt: install
    uv run python scripts/test_e2e.py --show-prompt

# Full API e2e test (uses real LLM API via FastAPI endpoints)
test-api FILE="": install
    #!/usr/bin/env bash
    if [ -n "{{ FILE }}" ]; then
        uv run python scripts/test_api_e2e.py --file "{{ FILE }}"
    else
        uv run python scripts/test_api_e2e.py
    fi

# Test API with text input
test-api-text TEXT: install
    uv run python scripts/test_api_e2e.py --text "{{ TEXT }}"

# List available models via API
test-api-models: install
    uv run python scripts/test_api_e2e.py --list-models

# Deploy to minikube
deploy-local:
    #!/usr/bin/env bash
    if [ ! -f deploy/local/secrets.env ]; then
        echo "Error: deploy/local/secrets.env not found"
        echo "Create it: cp deploy/local/secrets.env.example deploy/local/secrets.env"
        exit 1
    fi
    ./deploy/local/deploy.sh

# Remove local deployment
deploy-local-delete:
    ./deploy/local/deploy.sh --delete

# Remove build artifacts
clean:
    rm -rf .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
