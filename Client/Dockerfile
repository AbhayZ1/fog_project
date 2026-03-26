# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Create virtual environment
ENV VIRTUAL_ENV=/app/.venv
RUN uv venv

# Install dependencies
# We use uv pip install here since we don't have a localized pyproject.toml yet
# relying on the packages we know we need
# Use cache mount to speed up subsequent builds
# Use cache mount to speed up subsequent builds


RUN --mount=type=cache,target=/home/tba/.cache/uv \
    uv sync --link-mode=copy
# uv add torch torchvision flwr opacus numpy scikit-learn fastapi uvicorn

# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Install runtime system deps if needed (gl for opencv/torchvision)
RUN apt-get update && apt-get install -y libgl1 && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY client.py .
COPY architecture.py .
COPY ui.py .
COPY frontend ./frontend

# We expect data to be mounted at /app/data
ENV DATA_DIR=/app/data

# Entrypoint: Run ui.py (which launches client.py in bg)
ENTRYPOINT ["python", "ui.py"]
