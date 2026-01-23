# syntax=docker/dockerfile:1

# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev deps for production)
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/

# Test stage (for running tests in Docker)
FROM builder AS test

# Install dev dependencies for testing
RUN uv sync --frozen

# Copy test files
COPY tests/ ./tests/

# Run tests
CMD ["uv", "run", "pytest", "tests", "-v"]

# Production stage
FROM python:3.12-slim AS production

WORKDIR /app

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/src ./src

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV PYTHONUNBUFFERED=1

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

EXPOSE 8000

CMD ["uvicorn", "woo_hoo.main:app", "--host", "0.0.0.0", "--port", "8000"]
