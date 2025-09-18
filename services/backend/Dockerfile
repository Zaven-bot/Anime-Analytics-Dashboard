# Backend Dockerfile
FROM python:3.11-slim

# Commands will be run in in app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and set ownership
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose with "command:")
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]