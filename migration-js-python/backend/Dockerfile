FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including wait-for-it for database readiness
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    netcat-openbsd \
    libheif-dev \
    libde265-dev \
    libx265-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create wait script for database
RUN echo '#!/bin/bash\n\
    set -e\n\
    host="$1"\n\
    shift\n\
    cmd="$@"\n\
    until pg_isready -h "$host" -p 5432 -U aif_tracker; do\n\
    >&2 echo "Postgres is unavailable - sleeping"\n\
    sleep 1\n\
    done\n\
    >&2 echo "Postgres is up - executing command"\n\
    exec $cmd' > /wait-for-postgres.sh && chmod +x /wait-for-postgres.sh

# Expose port
EXPOSE 8000

# Wait for database and then start the application
CMD ["/wait-for-postgres.sh", "postgres", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "error"]
