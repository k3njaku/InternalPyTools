#!/usr/bin/env python3
"""
Pivot Codex V5 Launcher
========================

Simple launcher script for the Pivot Codex V5 application.
Automatically installs dependencies and starts the server.
"""

import subprocess
import sys
import os
from pathlib import Path

def install_requirements():
    """Install required packages if not already installed."""
    try:
        import fastapi
        import uvicorn
        import pandas
        print("✅ All required packages are already installed.")
        return True
    except ImportError:
        print("📦 Installing required packages...")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements_v5.txt"
            ])
            print("✅ Packages installed successfully!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install packages: {e}")
            return False

def create_static_dir():
    """Ensure static directory exists."""
    static_dir = Path("static")
    if not static_dir.exists():
        print("❌ Static directory not found. Please ensure static/ folder exists with index.html, style.css, and script.js")
        return False
    
    required_files = ["index.html", "style.css", "script.js"]
    missing_files = [f for f in required_files if not (static_dir / f).exists()]
    
    if missing_files:
        print(f"❌ Missing required static files: {', '.join(missing_files)}")
        return False
    
    print("✅ Static files found.")
    return True

def main():
    print("🚀 Pivot Codex V5 Launcher")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("CodexV2/pivot_by_codex_v5.py").exists():
        print("❌ pivot_by_codex_v5.py not found in CodexV2/ directory")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Create static directory
    if not create_static_dir():
        sys.exit(1)
    
    print("\n🌐 Starting Pivot Codex V5...")
    print("📊 Advanced Multi-Pivot Table Creator")
    print("🔗 Access at: http://localhost:8000")
    print("⚡ Press Ctrl+C to stop")
    print("=" * 40)
    
    # Start the server
    try:
        os.chdir("CodexV2")
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "pivot_by_codex_v5:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload",
            "--log-level", "info"
        ])
    except KeyboardInterrupt:
        print("\n👋 Pivot Codex V5 stopped.")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()