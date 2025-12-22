# =============================================================================
# AdSphere Moderation Service - Production Dockerfile
# =============================================================================
# Multi-stage build for smaller, secure production image
# =============================================================================

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Build wheels
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt


# Stage 2: Production
FROM python:3.11-slim as production

# Labels
LABEL maintainer="AdSphere Team"
LABEL version="1.0.0"
LABEL description="AI/ML Content Moderation Service"

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app
ENV PATH="${APP_HOME}/.local/bin:${PATH}"

WORKDIR $APP_HOME

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r moderation && useradd -r -g moderation moderation

# Copy wheels from builder
COPY --from=builder /build/wheels /wheels

# Install dependencies
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY --chown=moderation:moderation . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/models_weights /tmp/videos /tmp/images \
    && chown -R moderation:moderation /app /tmp/videos /tmp/images

# Switch to non-root user
USER moderation

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--loop", "uvloop", "--http", "httptools"]

