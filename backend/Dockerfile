# syntax=docker/dockerfile:1

##############
# Builder stage
##############
FROM python:3.13-slim AS builder

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv==0.12.12

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifests
COPY requirements.txt ./

# Install Python dependencies into a virtual environment
RUN uv venv /app/.venv && \
    VIRTUAL_ENV=/app/.venv uv pip install --no-cache-dir -r requirements.txt

##############
# Runner stage
##############
FROM python:3.13-slim AS runner

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Activate virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY . .

# Create non-root user
RUN addgroup --system app && adduser --system --group app
USER app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
