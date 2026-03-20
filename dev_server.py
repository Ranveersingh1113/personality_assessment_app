#!/usr/bin/env python3
"""
Development server with advanced file watching
Run this instead of streamlit run for enhanced development experience
"""

import subprocess
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

class ChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_streamlit()
    
    def start_streamlit(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        
        print("🚀 Starting Streamlit...")
        self.process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "frontend/streamlit_app.py",
            "--server.port", "8501",
            "--server.runOnSave", "true"
        ])
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith(('.py', '.toml')):
            print(f"🔄 File changed: {event.src_path}")
            # Streamlit handles its own reloading, so we don't restart here

if __name__ == "__main__":
    handler = ChangeHandler()
    observer = Observer()
    observer.schedule(handler, ".", recursive=True)
    observer.start()
    
    try:
        print("👀 Watching for file changes... Press Ctrl+C to stop")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if handler.process:
            handler.process.terminate()
    
    observer.join()