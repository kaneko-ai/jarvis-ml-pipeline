# JARVIS Research OS Docker Image
# Optimized for research workloads

FROM python:3.12-slim

# Labels
LABEL maintainer="kaneko-ai"
LABEL version="1.0.0"
LABEL description="JARVIS Research OS - AI-Powered Systematic Review Assistant"

# Environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

# Create app directory
WORKDIR /app

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --no-dev --frozen

# Copy application code
COPY . .

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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from jarvis_core import __version__; print(f'OK: {__version__}')" || exit 1

# Default command
ENTRYPOINT ["uv", "run", "python", "-m", "jarvis_core.cli"]
CMD ["--help"]
