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
# Use cache mount to speed up subsequent builds
# Use cache mount to speed up subsequent builds
RUN --mount=type=cache,target=/home/tba/.cache/uv \
    uv pip install torch torchvision flwr opacus numpy scikit-learn fastapi uvicorn multipart

# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.11-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY Central_Server/server.py Central_Server/server.py
COPY api.py .
COPY heatmap_generator.py .
COPY architecture.py .
COPY Central_Server/model_registry ./Central_Server/model_registry
COPY Central_Server/frontend ./frontend

# Create needed dirs
RUN mkdir -p static Central_Server

# Entrypoint: Run api.py (Orchestrator)
CMD ["python", "api.py"]
