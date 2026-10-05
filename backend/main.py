import os
import sys

# Ensure backend root is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Auto-switch to virtual environment if run with global python
venv_python = os.path.join(BASE_DIR, ".venv", "Scripts", "python.exe")
if os.path.exists(venv_python) and os.path.abspath(sys.executable).lower() != os.path.abspath(venv_python).lower():
    os.execv(venv_python, [venv_python, os.path.abspath(__file__)] + sys.argv[1:])

if __name__ == "__main__":
    import uvicorn
    print("Starting CCIP Backend on http://127.0.0.1:8000 ...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
