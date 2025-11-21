# Multi-stage Dockerfile for production

# Stage 1: Build dependencies
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    curl \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files and minimal source structure for installation
# Note: Build context must be project root for this to work
COPY backend-api/pyproject.toml ./
COPY backend-api/src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

# Stage 2: Runtime image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FFMPEG_VERSION=7.1 \
    PATH="/usr/local/bin:${PATH}"

WORKDIR /app

# Install runtime dependencies and FFmpeg static build
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    curl \
    xz-utils \
    ca-certificates \
    && curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
    -o /tmp/ffmpeg.tar.xz \
    && mkdir -p /tmp/ffmpeg \
    && tar -xf /tmp/ffmpeg.tar.xz -C /tmp/ffmpeg --strip-components=1 \
    && cp /tmp/ffmpeg/ffmpeg /usr/local/bin/ \
    && cp /tmp/ffmpeg/ffprobe /usr/local/bin/ \
    && chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe \
    && rm -rf /tmp/ffmpeg /tmp/ffmpeg.tar.xz \
    && apt-get purge -y curl xz-utils \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Verify FFmpeg installation
RUN ffmpeg -version && ffprobe -version

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser \
    && mkdir -p /app /tmp/ffmpeg \
    && chown -R appuser:appuser /app /tmp/ffmpeg

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser backend-api/src/ /app/src/

# Copy frontend build files (assumes build context is project root)
# These files are built by the frontend-app build process before Docker build
COPY --chown=appuser:appuser frontend-app/dist/ /app/frontend/dist/

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health').read()"

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
