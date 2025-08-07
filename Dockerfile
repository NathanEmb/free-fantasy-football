# Use Python 3.13 slim image
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install system dependencies including sqlite3
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy Python dependencies
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen

# Copy application code
COPY src/ ./src/
COPY static/ ./static/

# Copy database schema
COPY database/schema.sql ./database/schema.sql

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

ENV PYTHONPATH=/app

# Start services
CMD ["uv", "run", "src/main.py"]
