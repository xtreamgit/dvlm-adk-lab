# Backend API Dockerfile
FROM python:3.11-slim

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

# Suppress pip root user warning (safe in isolated Docker containers)
ENV PIP_ROOT_USER_ACTION=ignore

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code (build context is repo root)
COPY backend/src/ ./src/
COPY backend/config/ ./config/
COPY backend/migrations/ ./migrations/
COPY backend/add_missing_columns.py ./add_missing_columns.py
COPY backend/seed_data.py ./seed_data.py
COPY backend/entrypoint.sh ./entrypoint.sh
COPY environments/ ./environments/

# Create directory for SQLite database
RUN mkdir -p /app/data

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Set environment variables (only stable/non-sensitive defaults)
# Project-specific values should be set at deployment time via Cloud Run env vars
ENV PYTHONPATH=/app
ENV DATABASE_PATH=/app/data/users.db
ENV LOG_LEVEL=INFO
ENV ENVIRONMENT=production
# Note: PROJECT_ID, GOOGLE_CLOUD_LOCATION, VERTEXAI_PROJECT, VERTEXAI_LOCATION
# should be set via Cloud Run --set-env-vars during deployment
# Default values below are overridden by deployment configuration
ENV PROJECT_ID=adk-rag-ma
ENV GOOGLE_CLOUD_LOCATION=us-west1
ENV GOOGLE_GENAI_USE_VERTEXAI=true
ENV VERTEXAI_PROJECT=adk-rag-ma
ENV VERTEXAI_LOCATION=us-west1
ENV ACCOUNT_ENV=develom

# Set default PORT to match Cloud Run (Cloud Run will override this to 8080)
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application via entrypoint (runs migrations first)
CMD ["/app/entrypoint.sh"]
