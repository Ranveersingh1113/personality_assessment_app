@echo off
setlocal

echo ====================================================
echo   Student Personality Assessment System
echo   For Educational NGOs
echo ====================================================
echo.

REM Ensure we're in the script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    echo.
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version
echo.

REM Check if venv exists, create if not
if not exist .venv (
    echo [2/4] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo [2/4] Virtual environment already exists
)
echo.

REM Activate virtual environment and install dependencies
echo [3/4] Installing/updating dependencies...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
pip install -r requirements_visualization.txt --quiet
if errorlevel 1 (
    echo WARNING: Failed to install visualization dependencies
    echo The app will work but analytics dashboard may have limited features
)
echo Dependencies installed successfully!
echo.

REM Check if .env file exists
if not exist .env (
    echo WARNING: .env file not found!
    echo Please create a .env file with your Google API key
    echo Example: GOOGLE_API_KEY=your-api-key-here
    echo.
    echo You can still run the app in Developer Mode with local models
    echo.
)

REM Create necessary directories
if not exist assessments mkdir assessments
if not exist assessments\backups mkdir assessments\backups
if not exist sessions mkdir sessions

echo [4/4] Starting application...
echo.
echo ====================================================
echo   Application is starting...
echo ====================================================
echo.
echo The app will open in your default web browser at:
echo   http://localhost:8501
echo.
echo If it doesn't open automatically:
echo   1. Open your web browser
echo   2. Go to: http://localhost:8501
echo.
echo To STOP the application:
echo   - Press Ctrl+C in this window
echo   - Or close this window
echo.
echo ====================================================
echo.

REM Run the app
python -m streamlit run frontend/streamlit_app.py --server.port 8501 --server.headless true

REM If app exits, show message
echo.
echo Application has stopped.
echo.
pause
