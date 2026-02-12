# syntax=docker/dockerfile:1.4

# ===== Build Stage =====
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package installation
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install runtime dependencies + web extras (fastapi/uvicorn)
RUN uv sync --no-dev --extra web --frozen || uv sync --no-dev --extra web

# ===== Runtime Stage =====
FROM python:3.11-slim as runtime

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 jarvis

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY jarvis_core/ ./jarvis_core/
COPY jarvis_web/ ./jarvis_web/
COPY jarvis_cli.py ./

# Prepare writable runtime directories for non-root process
RUN mkdir -p /app/data/locks && chown -R jarvis:jarvis /app/data

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV JARVIS_LOG_LEVEL="INFO"

# Switch to non-root user
USER jarvis

# Health check (requests is usually in dependencies)
# If not, we might need to add it or use a simpler check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')" || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "-m", "uvicorn", "jarvis_web.app:app", "--host", "0.0.0.0", "--port", "8000"]
