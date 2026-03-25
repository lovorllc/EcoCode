"""
Launch uvicorn with fixed host/port so the server is reachable on the local network.
Run this with the project's Python interpreter (e.g. activate your venv first).
"""
import sys
import traceback

try:
    from main import app
except Exception as e:
    print("Failed to import app from main.py:", e)
    traceback.print_exc()
    sys.exit(1)

try:
    import uvicorn
except Exception as e:
    print("Missing uvicorn. Install with: python -m pip install uvicorn")
    sys.exit(1)

if __name__ == '__main__':
    # Bind to all interfaces on port 8000 for LAN access
    uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info', reload=False, proxy_headers=True, forwarded_allow_ips='*')
