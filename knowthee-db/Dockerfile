# Multi-stage Dockerfile for KnowThee Backend
# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

# Set work directory
WORKDIR /app

# Install system dependencies needed for building Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 knowthee && \
    mkdir -p /app/logs /app/data /app/chroma_db /app/employee_data && \
    chown -R knowthee:knowthee /app

# Set work directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/knowthee/.local

# Copy application code
COPY backend/ ./backend/

# Switch to non-root user
USER knowthee

# Add local bin to PATH
ENV PATH=/home/knowthee/.local/bin:$PATH

# Environment variables (can be overridden)
ENV PORT=8000
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["sleep", "infinity"] 