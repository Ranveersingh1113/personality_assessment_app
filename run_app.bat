@echo off
setlocal

echo Personality Assessment System for Rural Students
echo ====================================================
echo.

REM Ensure we're in the script directory
cd /d "%~dp0"

REM Check if venv exists, create if not
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Install dependencies
echo Installing dependencies...
".\venv\Scripts\python.exe" -m pip install --upgrade pip
".\venv\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo Starting Streamlit application...
echo.
echo The app will open in your default web browser.
echo If it doesn't open automatically, go to: http://localhost:8501
echo.
echo To stop the app, press Ctrl+C in this terminal
echo.

REM Run the app using the venv python to ensure correct environment
".\venv\Scripts\python.exe" -m streamlit run frontend/streamlit_app.py --server.port 8501

pause
