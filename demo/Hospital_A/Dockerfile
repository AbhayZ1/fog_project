FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (if any needed for opencv/etc)
RUN apt-get update && apt-get install -y libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*

# Copy requirements or pyproject.toml if available. 
# For this hackathon setup, we'll install deps directly.
RUN pip install torch torchvision flwr opacus numpy scikit-learn

COPY client_A.py .
COPY architecture.py .
COPY local_storage ./local_storage

CMD ["python", "client_A.py"]
