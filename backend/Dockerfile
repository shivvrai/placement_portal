FROM python:3.11-slim

WORKDIR /app

# System dependencies (libpq for asyncpg, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Application code
COPY . .

# Make entrypoint executable
RUN chmod +x /app/scripts/entrypoint.sh

EXPOSE 8000

# Default — overridden by entrypoint in docker-compose
CMD ["/bin/bash", "/app/scripts/entrypoint.sh"]
