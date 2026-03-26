import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import os
import threading
import sys
import subprocess

app = FastAPI()

# Path to built frontend
FRONTEND_DIR = Path("frontend")

@app.get("/")
async def read_root():
    return FileResponse(FRONTEND_DIR / "client.html")

# Mount static assets (JS, CSS)
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

def run_training_client():
    """Run the flower client in a separate thread/process"""
    print("🚀 Starting Flower Client...")
    # We call the existing client.py
    # Pass all arguments passed to this script to the client script
    cmd = [sys.executable, "client.py"] + sys.argv[1:]
    subprocess.Popen(cmd)

if __name__ == "__main__":
    # Start the training client in the background
    threading.Thread(target=run_training_client, daemon=True).start()
    
    print(f"🏥 Client Dashboard running on port 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
