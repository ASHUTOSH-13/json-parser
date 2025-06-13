# Use Python slim image for smaller size
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -r appuser && \
    chown appuser:appuser /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/uploads /app/outputs && \
    chown -R appuser:appuser /app/uploads /app/outputs && \
    chmod 755 /app/uploads /app/outputs

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create SQLite database directory with proper permissions
RUN mkdir -p /app/instance && \
    chown -R appuser:appuser /app/instance && \
    chmod 755 /app/instance

# Set proper permissions for all files
RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"] 