@echo off
setlocal enableextensions enabledelayedexpansion

echo 🎓 Personality Assessment System for Rural Students
echo ====================================================
echo.

REM Ensure we're in the script directory
cd /d "%~dp0"

REM Create a virtual environment if missing (avoid ensurepip by bootstrapping pip)
if not exist .venv (
    echo 🧪 Creating Python virtual environment (without pip)...
    py -m venv --without-pip .venv
)

REM If pip is missing inside venv, bootstrap it using get-pip.py
".venv\Scripts\python.exe" -m pip --version >nul 2>&1
if errorlevel 1 (
    echo 🌐 Downloading get-pip.py to bootstrap pip...
    powershell -Command "try { Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py' -UseBasicParsing } catch { exit 1 }"
    if exist get-pip.py (
        echo ⚙️  Installing pip into the virtual environment...
        ".venv\Scripts\python.exe" get-pip.py
        del get-pip.py
    ) else (
        echo ❌ Could not download get-pip.py. If you have conda, you can run:
        echo    conda create -n pa_app python=3.11 -y ^&^& conda activate pa_app ^&^& pip install -r requirements.txt ^&^& python -m streamlit run streamlit_app.py --server.port 8501
        goto :end
    )
)

REM Upgrade pip and install dependencies
echo 📦 Preparing environment...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if exist requirements.txt (
    echo 📥 Installing requirements...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
) else (
    echo ⚠️ requirements.txt not found, installing core packages...
    ".venv\Scripts\python.exe" -m pip install streamlit langchain langchain-google-genai langchain-community chromadb pydantic PyPDF2 sentence-transformers python-dotenv
)

echo.
echo 🚀 Starting Streamlit application...
echo.
echo The app will open in your default web browser.
echo If it doesn't open automatically, go to: http://localhost:8501
echo.
echo 📝 To stop the app, press Ctrl+C in this terminal
echo.

".venv\Scripts\python.exe" -m streamlit run frontend/streamlit_app.py --server.port 8501

pause
endlocal
:
:end
