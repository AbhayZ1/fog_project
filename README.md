# 🚀 Fed-X: Privacy-Preserving Federated Learning System for Medical Imaging

## 📌 Overview

Fed-X is a **production-style federated learning system** designed for medical image classification (Pneumonia detection) with:

* 🔐 Privacy-preserving training (Opacus)
* 🧠 Deep Learning (CNN - PyTorch)
* 🌐 Distributed clients (Hospitals A & B)
* 📊 Real-time monitoring dashboard
* 🔍 Explainable AI (Grad-CAM heatmaps)
* 🔄 Model versioning & rollback

---

## 🏗️ Architecture

```
                ┌────────────────────────┐
                │     Admin Dashboard    │
                │   (FastAPI + Frontend) │
                └──────────┬─────────────┘
                           │
                    REST + WebSocket
                           │
                ┌──────────▼──────────┐
                │   Central Server    │
                │  (Flower + FastAPI) │
                └──────────┬──────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                                     │
┌───────▼────────┐                  ┌─────────▼───────┐
│  Hospital A     │                  │  Hospital B     │
│  (Client Node)  │                  │  (Client Node)  │
└─────────────────┘                  └─────────────────┘
```

---

## 📂 Project Structure

```
.
├── api.py                     # Main FastAPI backend (orchestrator)
├── architecture.py           # CNN model definition
├── heatmap_generator.py      # Grad-CAM explainability
├── docker-compose.yml        # Multi-container setup
├── run_demo.py               # Local system launcher
│
├── Central_Server/           # Federated server
│   ├── server.py             # Flower server logic
│   ├── model_registry/       # Versioned models
│   └── frontend/             # Admin dashboard
│
├── Client/                   # Client node
│   ├── client.py             # Training logic
│   ├── ui.py                 # Local UI
│   └── frontend/             # Client dashboard
│
├── demo/                     # Simulated hospitals
│   ├── Hospital_A/
│   └── Hospital_B/
│
├── frontend/                 # Vite frontend (main UI)
│   ├── src/
│   └── dist/                 # Production build
│
└── dataset/                  # Generated dataset (after setup)
```

---

## ⚙️ Features

### 🧠 Federated Learning

* Flower-based distributed training
* Multiple client nodes (Hospitals)
* Non-IID data distribution

### 🔐 Privacy

* Differential Privacy using Opacus
* Epsilon tracking per round

### 📊 Monitoring Dashboard

* Real-time training metrics
* Accuracy, F1, fairness, privacy
* WebSocket-based live updates

### 🔍 Explainable AI

* Grad-CAM heatmaps
* Visual explanation of predictions

### 🔄 Model Management

* Versioning after each round
* Rollback to previous models
* Download checkpoints

---

## 🚀 Getting Started

### 1. Install dependencies

```bash
uv sync
```

### 2. Run system (local)

```bash
python run_demo.py
```

### 3. Open dashboard

```
http://localhost:8000
```

---

## 🐳 Run with Docker

```bash
docker-compose up --build
```

---

## 🔌 API Endpoints

| Endpoint                     | Description                 |
| ---------------------------- | --------------------------- |
| `/train/start`               | Start federated training    |
| `/train/stop`                | Stop training               |
| `/metrics`                   | Get training metrics        |
| `/predict`                   | Upload image for prediction |
| `/predict/explain`           | Prediction + heatmap        |
| `/models/versions`           | List model versions         |
| `/models/rollback/{version}` | Rollback model              |

---

## 📊 Dataset

* Based on **PneumoniaMNIST (MedMNIST)**
* Split into:

  * Hospital A (80% Normal)
  * Hospital B (80% Pneumonia)

---

## ⚠️ Known Issues

* Port inconsistencies (fix to single port recommended)
* Frontend serving duplication (needs cleanup)
* Hardcoded localhost in some configs

---

## 🧠 Future Improvements

* Kubernetes deployment
* Secure aggregation
* Real hospital integration
* Authentication system (JWT)

---

## 👤 Author

Abhay Mahantesh Zalaki

---

## 📜 License

MIT License
