# JARVIS Docker Configuration (AG-11)

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Copy project files
COPY pyproject.toml uv.lock ./
COPY jarvis_core ./jarvis_core
COPY jarvis_tools ./jarvis_tools
COPY jarvis_web ./jarvis_web
COPY dashboard ./dashboard
COPY scripts ./scripts
COPY evals ./evals
COPY docs ./docs

# Install dependencies
RUN ~/.local/bin/uv sync --frozen

# Create directories
RUN mkdir -p /app/logs/runs /app/data/uploads

# Environment
ENV PYTHONPATH=/app
ENV JARVIS_RUNS_DIR=/app/logs/runs
ENV JARVIS_UPLOADS_DIR=/app/data/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run
CMD ["~/.local/bin/uv", "run", "uvicorn", "jarvis_web.app:app", "--host", "0.0.0.0", "--port", "8000"]
