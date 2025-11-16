# Multi-stage Dockerfile for FastAPI Backend with FFmpeg
# Target: <500MB image size
# Features: Python 3.13, FFmpeg, static file serving, non-root user

# ============================================================================
# Stage 1: Builder - Install dependencies
# ============================================================================
FROM python:3.13-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================
# Stage 2: Runtime - Production image
# ============================================================================
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_HOME=/app

# Install runtime dependencies and FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Verify FFmpeg installation
RUN ffmpeg -version

# Create non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin -c "Application user" appuser

# Set working directory
WORKDIR ${APP_HOME}

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=appuser:appuser ./app ./app

# Create directory for frontend static files
RUN mkdir -p ${APP_HOME}/frontend/dist && \
    chown -R appuser:appuser ${APP_HOME}/frontend

# Create directory for temporary files and uploads
RUN mkdir -p ${APP_HOME}/temp ${APP_HOME}/uploads && \
    chown -R appuser:appuser ${APP_HOME}/temp ${APP_HOME}/uploads

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
