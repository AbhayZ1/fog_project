# -------- Base image --------
FROM python:3.11-slim

# -------- Install uv (package manager) --------
RUN pip install uv

# -------- Set work directory --------
WORKDIR /app

# -------- Copy project files --------
COPY . .

# -------- Install project dependencies --------
RUN uv sync --frozen

# -------- Expose API port --------
EXPOSE 8001

# -------- Command to run API --------
CMD ["uv", "run", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
