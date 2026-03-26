# 🚀 Fed-X: Federated Learning System for Medical Imaging

## 📌 What this project does

Fed-X is a **distributed AI system** that trains a pneumonia detection model across multiple hospitals **without sharing raw data**.

It includes:

* Federated learning (Flower)
* Differential privacy (Opacus)
* Real-time monitoring dashboard
* Explainable AI (Grad-CAM heatmaps)
* Model versioning + rollback

---

## 🧠 How the system works

1. Central server coordinates training
2. Multiple clients (Hospitals A & B) train locally
3. Model updates are aggregated (not raw data)
4. Dashboard shows live metrics

---

## 🏗️ Project Structure

```
.
├── api.py                     # Main backend (FastAPI orchestrator)
├── run_demo.py                # One-command local launcher
├── architecture.py            # CNN model
├── heatmap_generator.py       # Explainability (Grad-CAM)
│
├── Central_Server/            # Federated server (Flower)
├── Client/                    # Client training nodes
├── demo/                      # Simulated hospital datasets
├── frontend/                  # Web dashboard (Vite)
└── dataset/                   # Generated dataset (after setup)
```

---

## ⚙️ Prerequisites

* Python 3.11+
* Git
* (Optional) Docker

---

## 🚀 Quick Start (Local Setup)

### 1. Clone repo

```bash
git clone https://github.com/AbhayZ1/fog_project.git
cd fog_project
```

---

### 2. Install dependencies (IMPORTANT: uses `uv`)

```bash
pip install uv
uv sync
```

---

### 3. Download & prepare dataset

Run:

```bash
python setup_project.py
```

This will:

* Download PneumoniaMNIST
* Split into Hospital A & B
* Store in `dataset/`

---

### 4. Build frontend (only once)

```bash
cd frontend
npm install
npm run build
cd ..
```

---

### 5. Start the system

```bash
python run_demo.py
```

---

### 6. Open dashboard

```
http://localhost:8000
```

---

## 🎯 What you can do in the UI

* Start/stop federated training
* Monitor accuracy, fairness, privacy
* Upload X-ray image → get prediction
* View Grad-CAM heatmap
* Rollback model versions

---

## 🔌 Key API Endpoints

| Endpoint                     | Purpose              |
| ---------------------------- | -------------------- |
| `/train/start`               | Start training       |
| `/train/stop`                | Stop training        |
| `/metrics`                   | Get training metrics |
| `/predict`                   | Image prediction     |
| `/predict/explain`           | Prediction + heatmap |
| `/models/versions`           | List versions        |
| `/models/rollback/{version}` | Rollback             |

---

## 🐳 Docker Setup (Optional)

```bash
docker-compose up --build
```

---

## ⚠️ Common Issues

### 1. Port mismatch

Make sure backend runs on:

```
http://localhost:8000
```

---

### 2. Frontend not loading

Run:

```bash
npm run build
```

---

### 3. Model not found error

You must:

```
1. Run training first
OR
2. Ensure model file exists
```

---

### 4. Empty dashboard

Training not started yet:

```
Click "Start Training"
```

---

## 📊 Dataset Details

* Source: MedMNIST (PneumoniaMNIST)
* Non-IID split:

  * Hospital A → mostly NORMAL
  * Hospital B → mostly PNEUMONIA

---

## 🔐 Privacy

* Uses Differential Privacy (Opacus)
* Tracks epsilon per round

---

## 🔍 Explainability

* Grad-CAM heatmaps
* Highlights regions influencing prediction

---

## 🔄 Model Versioning

* Model saved after each round
* Can rollback to previous versions
* Stored in:

```
Central_Server/model_registry/
```

---

## 🧠 Tech Stack

* Backend: FastAPI, Python
* ML: PyTorch, Opacus
* Federated Learning: Flower
* Frontend: Vite, Vue
* Explainability: Grad-CAM

---

## 👤 Author

Abhay Mahantesh Zalaki

---

## 📜 License

MIT
