#!/usr/bin/env python3
"""
Startup script for the Personality Assessment System
Run this to launch the Streamlit web application
"""

import subprocess
import sys
import os

def main():
    print("🎓 Personality Assessment System for Rural Students")
    print("=" * 60)
    print()
    
    # Check if required files exist
    required_files = ["frontend/streamlit_app.py", "personality_assessment.py", "map-t.pdf"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print("❌ Missing required files:")
        for f in missing_files:
            print(f"   - {f}")
        print("\nPlease ensure all required files are present in the current directory.")
        return
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("⚠️  No .env file found. You'll need to enter your OpenAI API key in the app.")
        print("   Create a .env file with: OPENAI_API_KEY=your_api_key_here")
        print()
    
    print("✅ All required files found!")
    print()
    print("🚀 Starting Streamlit application...")
    print("   The app will open in your default web browser.")
    print("   If it doesn't open automatically, go to: http://localhost:8501")
    print()
    print("📝 To stop the app, press Ctrl+C in this terminal")
    print()
    
    try:
        # Run streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "frontend/streamlit_app.py", "--server.port", "8501"])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        print("\nTry running manually with:")
        print("   streamlit run streamlit_app.py")

if __name__ == "__main__":
    main()
