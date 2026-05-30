# Base Image
FROM python:3.12-slim

# System level optimization: Prevent Python from writing .pyc files & buffer outputs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set workspace
WORKDIR /workspace

# Install system dependencies (compiler/make tools not needed for our wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY app/ /workspace/app/
COPY raw_redis/ /workspace/raw_redis/

# Expose API port
EXPOSE 8000

# Default CMD (can be overridden in docker-compose for workers/flower)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
