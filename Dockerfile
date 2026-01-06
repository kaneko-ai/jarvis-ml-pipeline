# JARVIS Research OS Docker Image
# Multi-stage build for minimal production image

# --- Build Stage ---
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY jarvis_core/ ./jarvis_core/
COPY jarvis_tools/ ./jarvis_tools/
COPY jarvis_cli.py ./

# Install package
RUN pip install --no-cache-dir -e ".[embedding]"

# --- Production Stage ---
FROM python:3.12-slim as production

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app /app

# Create non-root user
RUN useradd -m -u 1000 jarvis
USER jarvis

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    JARVIS_HOME=/app \
    JARVIS_CACHE_DIR=/app/.cache

# Create cache directory
RUN mkdir -p /app/.cache

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from jarvis_core.sources import UnifiedSourceClient; print('OK')"

# Default command
CMD ["python", "-m", "jarvis_cli", "--help"]
