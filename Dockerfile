# JARVIS Research OS Docker Image
# Multi-stage build optimized for production

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.12-slim AS builder

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev --frozen

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.12-slim AS runtime

LABEL maintainer="kaneko-ai"
LABEL version="5.1.0"
LABEL description="JARVIS Research OS - AI-Powered Systematic Review Assistant"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY jarvis_core ./jarvis_core
COPY jarvis_cli.py ./
COPY pyproject.toml ./

# Create directories
RUN mkdir -p /app/data /app/artifacts /app/cache

# Set up non-root user
RUN useradd -m -u 1000 jarvis && \
    chown -R jarvis:jarvis /app
USER jarvis

# Environment variables
ENV JARVIS_DATA_DIR=/app/data
ENV JARVIS_CACHE_DIR=/app/cache
ENV JARVIS_ARTIFACTS_DIR=/app/artifacts
ENV JARVIS_OFFLINE=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from jarvis_core import __version__; print(f'OK: {__version__}')" || exit 1

# Default command
ENTRYPOINT ["python", "jarvis_cli.py"]
CMD ["--help"]

