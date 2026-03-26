import subprocess
import time
import sys
import os
import platform


def main():
    print("\n" + "="*50)
    print("   🚀 FED-X FOG SYSTEM LAUNCHER")
    print("="*50 + "\n")

    # 1. Start only the Backend (It serves the Frontend automatically)
    print("⚙️  Starting Fog Orchestrator on Port 5500...")
    
    # We run api.py directly which defaults to port 5500
    backend = subprocess.Popen(
        [sys.executable, "api.py"],
        stdout=sys.stdout, 
        stderr=sys.stderr 
    )

    print("⏳ Waiting for systems to initialize...")
    time.sleep(3)

    print("\n" + "="*50)
    print("✅ FOG NETWORK ONLINE")
    print("="*50)
    print("\n👉 ADMIN DASHBOARD: http://localhost:5500/admin_dashboard")
    print("👉 DOCTOR PORTAL:  http://localhost:5500/client_dashboard\n")

    try:
        while True:
            time.sleep(1)
            if backend.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Fog Orchestrator...")
        backend.terminate()


if __name__ == "__main__":
    main()
