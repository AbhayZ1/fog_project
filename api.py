print("Initializing Fed-X Backend...") 

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import subprocess
from pathlib import Path
import sys
import os
import time
import json
import asyncio
from typing import List
import torch
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import io
from architecture import get_model
from collections import OrderedDict
from opacus.validators import ModuleValidator
from heatmap_generator import generate_gradcam_heatmap, save_heatmap


# --- Configuration ---
from pydantic import BaseModel

# --- Configuration ---
# --- Configuration ---
METRICS_FILE = "fl_metrics.json"
MODEL_FILE = "Central_Server/global_model.pth"
SERVER_SCRIPT = "Central_Server/server.py"
CLIENT_SCRIPT = "Client/client.py"
DEVICE = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
# --- Change these three lines ---
ADMIN_DASHBOARD_PATH = Path("Central_Server/frontend/admin.html")
CLIENT_DASHBOARD_PATH = Path("Central_Server/frontend/client.html")

# ... later in the file near app.mount ...
print(f"✅ Device: {DEVICE}")
print(f"✅ Model file: {MODEL_FILE}")
print(f"✅ Metrics file: {METRICS_FILE}")

app = FastAPI(title="Fed-X API", version="1.0")

# Mount frontend assets
app.mount("/assets", StaticFiles(directory="Central_Server/frontend/assets"), name="assets")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ...

# Later in the file
@app.get("/client_dashboard", include_in_schema=False)
async def client_dashboard():
    """Serves the Client/Doctor dashboard."""
    if not CLIENT_DASHBOARD_PATH.exists():
        return HTMLResponse(content=f"<h1>Client Dashboard Not Found</h1><p>Expected at {CLIENT_DASHBOARD_PATH}</p>", status_code=404)
    return FileResponse(CLIENT_DASHBOARD_PATH, media_type="text/html")

@app.get("/admin_dashboard", include_in_schema=False)
async def admin_dashboard():
    """Serves the Admin dashboard."""
    if not ADMIN_DASHBOARD_PATH.exists():
        return HTMLResponse(content=f"<h1>Admin Dashboard Not Found</h1><p>Expected at {ADMIN_DASHBOARD_PATH}</p>", status_code=404)
    return FileResponse(ADMIN_DASHBOARD_PATH, media_type="text/html")


class LoginRequest(BaseModel):
    username: str
    password: str
    role: str

@app.post("/auth/login")
def login(request: LoginRequest):
    """Simple authentication endpoint"""
    if request.role == 'admin':
        if request.username == 'admin' and request.password == 'admin123':
            return {"token": "admin_secret_token", "role": "admin", "status": "authenticated"}
    elif request.role == 'doctor':
        if request.username == 'doctor' and request.password == 'fedx2025':
             return {"token": "doctor_secret_token", "role": "doctor", "status": "authenticated"}
    
    raise HTTPException(status_code=401, detail="Invalid Credentials")

training_processes = []
# ... (WebSocket Manager code remains here, implicitly, but we are just replacing the dashboard route block later)

# ... (We need to be careful not to delete ConnectionManager if we blindly replace. 
# The instruction says EndLine 146. Let's see what lines 28-146 cover.)
# Lines 28-39 are Config.
# Lines 40-49 are App setup.
# Lines 51-146 contain ConnectionManager, WebSocket, broadcast_state, health_check, dashboard_ui.
# I want to KEEP ConnectionManager and others, just CHANGE dashboard_ui and Config.

# BETTER PLAN:
# 1. Replace Config block (lines 28-35).
# 2. Replace dashboard_ui block (lines 127-146) with client/admin routes.
# 3. Insert LoginRequest and /auth/login somewhere (maybe after app instantiation or before routes).


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_state():
    """Background task to broadcast training state and metrics"""
    while True:
        # Check training status
        active_processes = [p for p in training_processes if p.poll() is None]
        is_training = len(active_processes) > 0
        
        # Get metrics
        metrics = []
        if os.path.exists(METRICS_FILE) and os.path.getsize(METRICS_FILE) > 0:
            try:
                with open(METRICS_FILE, 'r') as f:
                    metrics = json.load(f)
            except:
                pass
        
        await manager.broadcast({
            "is_training": is_training,
            "metrics": metrics,
            "active_processes": len(active_processes)
        })
        
        await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(broadcast_state())


@app.get("/")
def health_check():
    """Health check endpoint"""
    model_exists = os.path.exists(MODEL_FILE)
    model_size = os.path.getsize(MODEL_FILE) / (1024 * 1024) if model_exists else 0
    
    return {
        "status": "online", 
        "system": "Fed-X Orchestrator",
        "device": str(DEVICE),
        "model_trained": model_exists,
        "model_size_mb": round(model_size, 2) if model_exists else 0
    }

@app.get("/dashboard")
async def dashboard_redirect():
     return HTMLResponse(
         """
         <body style="background: #0f172a; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh;">
            <div style="text-align: center; background: #1e293b; padding: 3rem; border-radius: 1rem; border: 1px solid #334155;">
                <h1 style="margin-bottom: 2rem;">Fed-X Secure Portal</h1>
                <div style="display: flex; gap: 1rem;">
                    <a href='/admin_dashboard' style="display: block; padding: 1rem 2rem; background: #7c3aed; color: white; text-decoration: none; border-radius: 0.5rem; font-weight: bold;">
                        Admin Console (Server)
                    </a>
                </div>
                <p style="margin-top: 1.5rem; color: #94a3b8; font-size: 0.9rem;">
                    Note: Client Dashboard is served by the Client Node (Hospital A/B).
                </p>
            </div>
         </body>
         """
     )


@app.post("/train/start")
def start_training():
    """Start federated learning training process"""
    global training_processes
    
    # Stop any existing processes
    if training_processes:
        print("⚠️  Stopping existing training processes...")
        stop_training()
    
    # Clean up old metrics
    if os.path.exists(METRICS_FILE):
        os.remove(METRICS_FILE)
        print(f"🧹 Deleted old metrics: {METRICS_FILE}")
    
    try:
        # Launch Server (without capturing output)
        print("\n" + "="*70)
        print("🚀 Launching Server Process...")
        p_server = subprocess.Popen([sys.executable, SERVER_SCRIPT])
        training_processes.append(p_server)
        print(f"✅ Server PID: {p_server.pid}")
        
        # Launch Client A
        print("🏥 Launching Client A (Hospital_A)...")
        p_a = subprocess.Popen([
            sys.executable, 
            CLIENT_SCRIPT, 
            "--client_id", "Hospital_A",
            "--data_dir", "demo/Hospital_A/local_storage/data"
        ])
        training_processes.append(p_a)
        print(f"✅ Client A PID: {p_a.pid}")
        
        # Launch Client B
        print("🏥 Launching Client B (Hospital_B)...")
        p_b = subprocess.Popen([
            sys.executable, 
            CLIENT_SCRIPT, 
            "--client_id", "Hospital_B",
            "--data_dir", "demo/Hospital_B/local_storage/data"
        ])
        training_processes.append(p_b)
        print(f"✅ Client B PID: {p_b.pid}")
        print("="*70 + "\n")
        
        return {
            "message": "Federated Protocol Initialized", 
            "server_pid": p_server.pid,
            "client_a_pid": p_a.pid,
            "client_b_pid": p_b.pid,
            "total_processes": len(training_processes)
        }
        
    except Exception as e:
        print(f"❌ Failed to start training: {e}")
        stop_training()
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")


@app.post("/train/stop")
def stop_training():
    """Stop all federated learning processes"""
    global training_processes
    
    if not training_processes:
        return {"message": "No active training processes"}
    
    stopped_count = 0
    for p in training_processes:
        try:
            p.terminate()
            p.wait(timeout=5)
            stopped_count += 1
        except subprocess.TimeoutExpired:
            p.kill()  # Force kill if doesn't terminate
            stopped_count += 1
        except Exception as e:
            print(f"⚠️  Error stopping process {p.pid}: {e}")
    
    training_processes = []
    print(f"🛑 Stopped {stopped_count} training process(es)")
    
    return {
        "message": "Protocol Terminated", 
        "processes_stopped": stopped_count
    }


@app.get("/metrics")
def get_metrics():
    """Get current training metrics"""
    if not os.path.exists(METRICS_FILE):
        return JSONResponse(content=[], status_code=200)
    
    try:
        # Check if file is empty
        if os.path.getsize(METRICS_FILE) == 0:
            return JSONResponse(content=[], status_code=200)
        
        with open(METRICS_FILE, 'r') as f:
            data = json.load(f)
        
        # Ensure data is a list
        if not isinstance(data, list):
            return JSONResponse(content=[], status_code=200)
        
        return JSONResponse(content=data, status_code=200)
        
    except json.JSONDecodeError:
        print("⚠️  Metrics file contains invalid JSON")
        return JSONResponse(content=[], status_code=200)
    except Exception as e:
        print(f"⚠️  Error reading metrics: {e}")
        return JSONResponse(content=[], status_code=200)


@app.get("/training/status")
def get_training_status():
    """Get current training status"""
    active_processes = [p for p in training_processes if p.poll() is None]
    
    return {
        "is_training": len(active_processes) > 0,
        "active_processes": len(active_processes),
        "total_processes": len(training_processes),
        "model_exists": os.path.exists(MODEL_FILE),
        "metrics_exist": os.path.exists(METRICS_FILE)
    }


@app.post("/predict")
async def predict_image(file: UploadFile = File(...)):
    """
    Predict pneumonia from chest X-ray image.
    
    Args:
        file: Uploaded image file (JPEG/PNG/BMP)
    
    Returns:
        JSON with prediction, confidence, and probabilities
    """
    
    # 1. Check if model exists
    if not os.path.exists(MODEL_FILE):
        raise HTTPException(
            status_code=400, 
            detail="Model not trained yet. Please complete training in the Network Ops tab first."
        )
    
    # 2. Validate model file size
    model_size_mb = os.path.getsize(MODEL_FILE) / (1024 * 1024)
    if model_size_mb < 1.0:
        print(f"⚠️  WARNING: Model file is only {model_size_mb:.2f} MB - may be untrained")
    
    try:
        # 3. Read and validate image
        contents = await file.read()
        
        try:
            image = Image.open(io.BytesIO(contents))
        except Exception as img_error:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid image file. Please upload a valid JPEG/PNG image. Error: {str(img_error)}"
            )
        
        # 4. Convert to grayscale if needed
        if image.mode not in ['L', 'RGB']:
            image = image.convert('RGB')
        
        # 5. Apply preprocessing (same as training)
        transform = transforms.Compose([
            transforms.Grayscale(num_output_channels=1),
            transforms.Resize((28, 28)),
            transforms.ToTensor()
        ])
        
        img_t = transform(image).unsqueeze(0).to(DEVICE)
        
        # 6. Load model with correct architecture (BatchNorm → GroupNorm)
        model = get_model()
        model = ModuleValidator.fix(model)  # Apply same fix as training
        model = model.to(DEVICE)
        model.eval()
        
        print(f"✅ Model architecture prepared (device: {DEVICE})")
        
        # 7. Load trained weights
        try:
            state_dict = torch.load(MODEL_FILE, map_location=DEVICE)
            model.load_state_dict(state_dict, strict=True)
            print(f"✅ Model weights loaded successfully")
        except RuntimeError as load_error:
            print(f"❌ Failed to load model: {load_error}")
            raise HTTPException(
                status_code=500, 
                detail=f"Model loading failed. The model may be corrupted or incompatible. Please retrain. Error: {str(load_error)}"
            )
        
        # 8. Run inference with safety checks
        with torch.no_grad():
            outputs = model(img_t)
            
            # Debug: Print raw outputs
            print(f"🔍 Raw model outputs: {outputs[0].tolist()}")
            
            # Apply softmax to get probabilities
            probabilities = F.softmax(outputs, dim=1)
            
            # Debug: Print probabilities
            print(f"🔍 Softmax probabilities: {probabilities[0].tolist()}")
            
            # Get prediction and confidence
            confidence, predicted = torch.max(probabilities, 1)

        # 9. Map prediction to class name
        class_names = ["NORMAL", "PNEUMONIA"]
        prediction = class_names[predicted.item()]

        # Extract individual probabilities
        normal_prob = probabilities[0][0].item()
        pneumonia_prob = probabilities[0][1].item()

        # Clamp values to [0, 1] range for safety
        normal_prob = max(0.0, min(1.0, normal_prob))
        pneumonia_prob = max(0.0, min(1.0, pneumonia_prob))
        confidence_score = max(0.0, min(1.0, confidence.item()))

        print(f"📊 Prediction: {prediction}")
        print(f"   Confidence: {confidence_score*100:.2f}%")
        print(f"   Normal: {normal_prob*100:.2f}% | Pneumonia: {pneumonia_prob*100:.2f}%")

        return {
            "prediction": prediction,
            "confidence": round(confidence_score * 100, 2),
            "probabilities": {
                "normal": round(normal_prob * 100, 2),
                "pneumonia": round(pneumonia_prob * 100, 2)
            },
            "model_size_mb": round(model_size_mb, 2),
            "device": str(DEVICE)
        }
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        print(f"❌ Unexpected error during prediction: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post("/predict/explain")
async def predict_with_explanation(file: UploadFile = File(...)):
    """
    Predict pneumonia AND generate explainability heatmap.
    Shows WHERE in the X-ray the model is looking.
    
    Args:
        file: Uploaded X-ray image
    
    Returns:
        Prediction + confidence + heatmap URL
    """
    
    if not os.path.exists(MODEL_FILE):
        raise HTTPException(
            status_code=400, 
            detail="Model not trained yet. Please complete training first."
        )
    
    try:
        # 1. Read and preprocess image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Apply same preprocessing as training
        transform = transforms.Compose([
            transforms.Grayscale(num_output_channels=1),
            transforms.Resize((28, 28)),
            transforms.ToTensor()
        ])
        
        img_t = transform(image).unsqueeze(0).to(DEVICE)
        
        # 2. Load model with correct architecture
        model = get_model()
        model = ModuleValidator.fix(model)
        model = model.to(DEVICE)
        model.eval()
        
        # 3. Load trained weights
        state_dict = torch.load(MODEL_FILE, map_location=DEVICE)
        model.load_state_dict(state_dict, strict=True)
        
        # 4. Generate Grad-CAM heatmap
        print("🔍 Generating Grad-CAM heatmap...")
        heatmap_data = generate_gradcam_heatmap(model, img_t)
        
        # 5. Save heatmap
        heatmap_path = save_heatmap(heatmap_data, "static/heatmap_latest.png")
        print(f"✅ Heatmap saved to {heatmap_path}")
        
        # 6. Get prediction details
        prediction = heatmap_data["prediction"]
        confidence = heatmap_data["confidence"]
        class_names = ["NORMAL", "PNEUMONIA"]
        
        # 7. Get probabilities from model
        with torch.no_grad():
            outputs = model(img_t)
            probabilities = F.softmax(outputs, dim=1)
            normal_prob = probabilities[0][0].item()
            pneumonia_prob = probabilities[0][1].item()
        
        # Clamp values
        normal_prob = max(0.0, min(1.0, normal_prob))
        pneumonia_prob = max(0.0, min(1.0, pneumonia_prob))
        confidence = max(0.0, min(1.0, confidence))
        
        print(f"📊 Prediction: {class_names[prediction]} ({confidence*100:.2f}%)")
        
        return {
            "prediction": class_names[prediction],
            "confidence": round(confidence * 100, 2),
            "probabilities": {
                "normal": round(normal_prob * 100, 2),
                "pneumonia": round(pneumonia_prob * 100, 2)
            },
            "heatmap_url": "/static/heatmap_latest.png",
            "explainability": "Heatmap shows areas the AI focused on for diagnosis"
        }
        
    except Exception as e:
        print(f"❌ Error generating explanation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate explanation: {str(e)}"
        )

@app.get("/models/versions")
def list_model_versions():
    """List all available model versions with metadata"""
    # Dynamically import helper from new location
    sys.path.append(os.path.join(os.path.dirname(__file__), "Central_Server"))
    from server import get_version_history
    
    versions = get_version_history()
    
    # Load metrics to attach accuracy to each version
    if os.path.exists(METRICS_FILE) and os.path.getsize(METRICS_FILE) > 0:
        try:
            with open(METRICS_FILE, 'r') as f:
                metrics = json.load(f)
            
            # Create a mapping of round -> metrics
            metrics_map = {m['round']: m for m in metrics}
            
            # Attach metrics to versions
            for v in versions:
                round_metrics = metrics_map.get(v['version'], {})
                v['accuracy'] = round_metrics.get('test_accuracy', 0.0)
                v['privacy_epsilon'] = round_metrics.get('privacy_epsilon', 0.0)
                v['fairness_score'] = round_metrics.get('fairness_score', 1.0)
        except:
            pass
    
    return {
        "total_versions": len(versions),
        "versions": versions
    }


@app.post("/models/rollback/{version}")
def rollback_to_version(version: int):
    """Rollback to a specific model version"""
    try:
        version_file = os.path.join("Central_Server", "model_registry", f"model_v{version}.pth")
        
        if not os.path.exists(version_file):
            return {"error": f"Version {version} not found"}
        
        # Load the versioned checkpoint
        checkpoint = torch.load(version_file, map_location='cpu')
        
        # Save as current global model
        torch.save(checkpoint['model_state_dict'], MODEL_FILE)
        
        print(f"✅ Rolled back to model version {version}")
        
        return {
            "success": True,
            "message": f"Successfully rolled back to version {version}",
            "version": version,
            "timestamp": checkpoint.get('timestamp', 'Unknown')
        }
        
    except Exception as e:
        return {"error": str(e)}


@app.get("/models/download/{version}")
def download_model_version(version: int):
    """Download a specific model version"""
    from fastapi.responses import FileResponse
    
    version_file = os.path.join("Central_Server", "model_registry", f"model_v{version}.pth")
    
    if not os.path.exists(version_file):
        return {"error": f"Version {version} not found"}
    
    return FileResponse(
        path=version_file,
        filename=f"federated_model_v{version}.pth",
        media_type="application/octet-stream"
    )

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up processes on API shutdown"""
    print("\n🛑 Shutting down API - cleaning up training processes...")
    stop_training()
    print("✅ Cleanup complete")


# Mount static directory for serving heatmap images
if not os.path.exists("static"):
    os.makedirs("static")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/feedback")
async def submit_feedback(
    file: UploadFile = File(...),
    prediction: str = Form(...),
    correct_label: str = Form(...),
    heatmap_feedback: str = Form(...),
    comments: str = Form(None)
):
    """
    Submit manual feedback for a prediction.
    """
    try:
        # 1. Create feedback directory
        feedback_dir = Path("dataset/feedback_data")
        feedback_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. Save image
        timestamp = int(time.time())
        filename = f"{timestamp}_{correct_label.lower()}.png"
        file_path = feedback_dir / filename
        
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
            
        # 3. Save metadata
        feedback_entry = {
            "timestamp": timestamp,
            "image_path": str(file_path),
            "model_prediction": prediction,
            "user_correction": correct_label,
            "heatmap_feedback": heatmap_feedback,
            "comments": comments,
            "status": "pending_review"
        }
        
        log_file = Path("feedback_log.json")
        if log_file.exists():
            with open(log_file, "r") as f:
                logs = json.load(f)
        else:
            logs = []
            
        logs.append(feedback_entry)
        
        with open(log_file, "w") as f:
            json.dump(logs, f, indent=2)
            
        print(f"✅ Feedback received: {correct_label} (Heatmap: {heatmap_feedback})")
        
        return {
            "message": "Feedback received successfully. The model will be updated in the next training cycle.",
            "status": "success"
        }
        
    except Exception as e:
        print(f"❌ Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Run Server ---
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 Starting Fed-X API Server")
    print("="*70)
    print(f"Dashboard:  http://localhost:5500/dashboard")
    print(f"API Docs:   http://localhost:5500/docs")
    print(f"Health:     http://localhost:5500/")
    print("="*70 + "\n")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=5500,
        log_level="info"
    )
