FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y libgl1-mesa-glx && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install torch torchvision flwr opacus numpy scikit-learn

COPY client_B.py .
COPY architecture.py .
COPY local_storage ./local_storage

CMD ["python", "client_B.py"]
