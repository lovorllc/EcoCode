"""Simple launcher for running the FastAPI app when packaged with PyInstaller.

Use this as the entrypoint for PyInstaller (instead of `main.py`).
"""
import os
import sys

# Ensure current dir is set to the executable's folder when frozen
if getattr(sys, 'frozen', False):
    os.chdir(getattr(sys, '_MEIPASS', os.getcwd()))

# Import the FastAPI app and server library with friendly error messages
import traceback
try:
    from main import app
except Exception as e:
    print("Failed to import the application (main.py).")
    print("Make sure the virtualenv is active and dependencies are installed: python -m pip install -r requirements.txt")
    print("Exception:", e)
    traceback.print_exc()
    sys.exit(1)

try:
    import uvicorn
except Exception as e:
    print("Missing required package 'uvicorn'. Install it with: python -m pip install uvicorn")
    print("Or install all requirements: python -m pip install -r requirements.txt")
    print("Exception:", e)
    sys.exit(1)

if __name__ == '__main__':
    # Force host/port per project requirement: always bind 0.0.0.0:8000
    host = '0.0.0.0'
    port = 800
    print(f"Starting server at http://{host}:{port} (Ctrl+C to stop)")
    # Use reload=False in frozen bundles; uvicorn reload uses file watching unavailable in exe
    try:
        uvicorn.run(app, host=host, port=port, log_level='info', reload=False)
    except Exception as e:
        print("Uvicorn failed to start. Ensure dependencies are installed and the port is free.")
        print("Exception:", e)
        traceback.print_exc()
        sys.exit(1)
