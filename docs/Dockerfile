# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps for asyncpg + hiredis
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements first (caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

EXPOSE 8000