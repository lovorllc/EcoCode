# EcoCode Auto-Start Script
Write-Host "Starting EcoCode server..." -ForegroundColor Green

# Check if virtual environment exists
if (!(Test-Path ".venv\Scripts\activate.ps1")) {
    Write-Host "Virtual environment not found. Creating one..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "Installing requirements..." -ForegroundColor Yellow
    & ".venv\Scripts\activate.ps1"
    python -m pip install -r requirements.txt
} else {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & ".venv\Scripts\activate.ps1"
}

# Check if requirements are installed
try {
    python -c "import fastapi, uvicorn" 2>$null
} catch {
    Write-Host "Installing missing requirements..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
}

# Start the server
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Cyan
python uvicorn_fixed.py