  FROM python:3.11-slim AS builder

  # Set environment variables
  ENV PYTHONDONTWRITEBYTECODE=1 \
      PYTHONUNBUFFERED=1 \
      PIP_NO_CACHE_DIR=1 \
      PIP_DISABLE_PIP_VERSION_CHECK=1

  # Install build dependencies
  # RUN apt-get update && apt-get install -y \
  #     build-essential \
  #     gcc \
  #     g++ \
  #     libgdal-dev \
  #     libspatialindex-dev \
  #     && rm -rf /var/lib/apt/lists/*

  # Install Python dependencies
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install --no-cache-dir -r requirements.txt

  # Second stage - runtime image
  FROM python:3.11-slim

  # Set environment variables
  ENV PYTHONDONTWRITEBYTECODE=1 \
      PYTHONUNBUFFERED=1 \
      PYTHONPATH=/app \
      LOG_LEVEL=INFO

  # Install runtime system dependencies
  # RUN apt-get update && apt-get install -y \
  #     libgdal30 \
  #     libspatialindex6 \
  #     curl \
  #     && rm -rf /var/lib/apt/lists/*

  # Create non-root user
  RUN useradd --create-home appuser
  WORKDIR /app

  # Copy Python packages from builder stage
  COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
  COPY --from=builder /usr/local/bin /usr/local/bin

  # Copy application code
  COPY --chown=appuser:appuser . .

  # Switch to non-root user
  USER appuser

  # Health check
  HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
      CMD curl -f http://localhost:8000/health || exit 1

  # Expose port
  EXPOSE 8000

  # Run the application
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]