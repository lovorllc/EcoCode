@echo off
REM EcoCode Auto-Start Script
echo Starting EcoCode server...

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating one...
    python -m venv .venv
    echo Installing requirements...
    call .venv\Scripts\activate.bat
    python -m pip install -r requirements.txt
) else (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Check if requirements are installed
python -c "import fastapi, uvicorn" 2>nul
if errorlevel 1 (
    echo Installing missing requirements...
    python -m pip install -r requirements.txt
)

REM Start the server
REM Start ngrok (runs in a separate window so server logs remain visible)
echo Preparing ngrok...
if exist "ngrok\ngrok.exe" (
    echo Found ngrok executable.
    REM Set default auth token if not provided via environment variable
    if not defined NGROK_AUTH_TOKEN (
        set NGROK_AUTH_TOKEN=37suXzICbjBMXSNOI6mCmeg08cJ_WfmaY56kCacRc8dHFt7z
    )
    echo Configuring ngrok auth token...
    "%~dp0ngrok\ngrok.exe" authtoken %NGROK_AUTH_TOKEN% >nul 2>&1
    start "" "%~dp0ngrok\ngrok.exe" http 8000 --log=ngrok.log
) else if exist "ngrok.zip" (
    echo Extracting ngrok.zip to ngrok\ ...
    powershell -NoProfile -Command "Expand-Archive -Force -Path '%~dp0ngrok.zip' -DestinationPath '%~dp0ngrok'" >nul 2>&1
    if exist "ngrok\ngrok.exe" (
        REM Set default auth token if not provided via environment variable
        if not defined NGROK_AUTH_TOKEN (
            set NGROK_AUTH_TOKEN=37suXzICbjBMXSNOI6mCmeg08cJ_WfmaY56kCacRc8dHFt7z
        )
        echo Configuring ngrok auth token...
        "%~dp0ngrok\ngrok.exe" authtoken %NGROK_AUTH_TOKEN% >nul 2>&1
        start "" "%~dp0ngrok\ngrok.exe" http 8000 --log=ngrok.log
    ) else (
        echo Warning: ngrok.exe not found after extraction. Please place ngrok.exe into the ngrok\ folder.
    )
) else (
    echo Warning: ngrok not found. Place ngrok.exe in ngrok\ or put ngrok.zip in workspace.
)

echo Starting server on http://localhost:8000
python uvicorn_fixed.py

PAUSE
