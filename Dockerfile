# Production Dockerfile
# RP-500: Optimized multi-stage build for JARVIS

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.lock ./
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.lock

# ============================================
# Stage 2: Production
# ============================================
FROM python:3.11-slim as production

# Labels
LABEL maintainer="JARVIS Team"
LABEL version="4.4"
LABEL description="JARVIS Research OS Production Image"

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    JARVIS_ENV=production

# Create non-root user
RUN groupadd --gid 1000 jarvis \
    && useradd --uid 1000 --gid jarvis --shell /bin/bash --create-home jarvis

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy wheels from builder
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy application
COPY --chown=jarvis:jarvis jarvis_core/ ./jarvis_core/
COPY --chown=jarvis:jarvis jarvis_tools/ ./jarvis_tools/
COPY --chown=jarvis:jarvis jarvis_web/ ./jarvis_web/
COPY --chown=jarvis:jarvis scripts/ ./scripts/
COPY --chown=jarvis:jarvis run_pipeline.py ./

# Create directories
RUN mkdir -p /app/logs /app/data /app/cache \
    && chown -R jarvis:jarvis /app

# Switch to non-root user
USER jarvis

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["python", "-m", "uvicorn", "jarvis_web.app:app", "--host", "0.0.0.0", "--port", "8000"]
