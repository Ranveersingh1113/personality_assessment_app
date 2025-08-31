@echo off
echo 🎓 Personality Assessment System for Rural Students
echo ====================================================
echo.
echo 🚀 Starting Streamlit application...
echo.
echo The app will open in your default web browser.
echo If it doesn't open automatically, go to: http://localhost:8501
echo.
echo 📝 To stop the app, press Ctrl+C in this terminal
echo.

python -m streamlit run streamlit_app.py --server.port 8501

pause
