#!/usr/bin/env python3
"""
MotionScript – Direct Python launcher.
Use this if you prefer `python3 run.py` over `./run.sh`.
"""

import subprocess
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(PROJECT_DIR, "venv", "bin", "python")
APP_PATH = os.path.join(PROJECT_DIR, "app.py")

def main():
    # If running inside the venv already, just launch the app
    if os.environ.get("VIRTUAL_ENV") or not os.path.exists(VENV_PYTHON):
        # Direct run (user activated venv manually, or no venv)
        os.chdir(PROJECT_DIR)
        sys.path.insert(0, PROJECT_DIR)
        from app import app
        print("\n  Starting MotionScript...")
        print("  Open http://localhost:5000 in your browser")
        print("  Press Ctrl+C to stop\n")
        app.run(host="0.0.0.0", port=5000, debug=True)
    else:
        # Re-launch under the venv python
        os.execv(VENV_PYTHON, [VENV_PYTHON, APP_PATH])


if __name__ == "__main__":
    main()
