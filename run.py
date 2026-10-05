"""
CCIP — One-Command Runner
Run everything with a single simple command:
    python run.py           -> Starts both Backend (port 8000) & Frontend (port 5173)
    python run.py backend   -> Starts Backend only
    python run.py frontend  -> Starts Frontend only
"""

import os
import sys
import subprocess
import signal

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
VENV_PYTHON = os.path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")

def get_python_exe():
    if os.path.exists(VENV_PYTHON):
        return VENV_PYTHON
    return sys.executable

def start_backend():
    py = get_python_exe()
    cmd = [py, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    print("🚀 [Backend] Starting FastAPI on http://127.0.0.1:8000 ...")
    return subprocess.Popen(cmd, cwd=BACKEND_DIR)

def start_frontend():
    # Use npm.cmd on Windows
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    cmd = [npm_cmd, "run", "dev"]
    print("⚡ [Frontend] Starting Vite on http://localhost:5173 ...")
    return subprocess.Popen(cmd, cwd=FRONTEND_DIR)

def main():
    target = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    procs = []

    try:
        if target in ("all", "backend"):
            procs.append(start_backend())

        if target in ("all", "frontend"):
            procs.append(start_frontend())

        print("\n✅ CCIP is running!")
        print("   • Frontend : http://localhost:5173")
        print("   • Backend  : http://127.0.0.1:8000")
        print("   • API Docs : http://127.0.0.1:8000/docs")
        print("\nPress Ctrl+C to stop all servers.\n")

        for p in procs:
            p.wait()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers...")
        for p in procs:
            try:
                p.terminate()
            except Exception:
                pass
        print("Done.")

if __name__ == "__main__":
    main()
