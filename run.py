import os
import sys
import subprocess
import time
from pathlib import Path

def main() -> None:
    # Project root
    root = Path(__file__).parent.resolve()
    # Ensure project root and frontend are on PYTHONPATH for consistent imports
    os.environ.setdefault("PYTHONPATH", str(root))
    
    # Backend: uvicorn backend.main:app
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        os.environ.get("BACKEND_PORT", "8000"),
        "--reload",
        "--log-level",  # Add log level for backend
        "debug",
    ]
    
    # Frontend: streamlit run frontend/streamlit_app.py with debug flags
    frontend_cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(root / "frontend" / "streamlit_app.py"),
        "--server.port",
        os.environ.get("FRONTEND_PORT", "8501"),
        "--server.headless",
        "true",
        "--server.runOnSave",  # Enable run on save
        "true",
        "--logger.level",  # Set logger level to debug
        "debug",
        "--theme.base",  # Optional: Set light theme for better visibility of errors
        "light",
        "--client.showSidebarNavigation",  # Optional: Show sidebar navigation
        "false",
    ]
    clear_logs = [
        "cmd.exe",
        "/c",
        "cls"
    ] if os.name == "nt" else [
        "clear"
    ]
    
    # Start backend first
    print("Starting backend (FastAPI) ...")
    backend_proc = subprocess.Popen(clear_logs, cwd=str(root))
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(root))
    
    # Wait briefly to let backend start
    time.sleep(2)
    
    # Start frontend
    print("Starting frontend (Streamlit) in debug mode ...")
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(root / "frontend"))
    
    print("\nServices started:")
    print(f"- Backend: http://localhost:{os.environ.get('BACKEND_PORT', '8000')}")
    print(f"- Frontend: http://localhost:{os.environ.get('FRONTEND_PORT', '8501')}")
    print("Press Ctrl+C to stop.")
    
    try:
        # Wait for either process to exit
        while True:
            backend_code = backend_proc.poll()
            frontend_code = frontend_proc.poll()
            if backend_code is not None:
                print(f"Backend exited with code {backend_code}.")
                break
            if frontend_code is not None:
                print(f"Frontend exited with code {frontend_code}.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        for proc in (frontend_proc, backend_proc):
            if proc.poll() is None:
                proc.terminate()
        for proc in (frontend_proc, backend_proc):
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

if __name__ == "__main__":
    main()