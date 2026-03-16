#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# MotionScript – Launch the app
# ──────────────────────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

# Check if setup was run
if [ ! -d "$VENV_DIR" ]; then
    echo "Virtual environment not found. Running setup first..."
    echo ""
    bash "$SCRIPT_DIR/setup.sh"
fi

echo ""
echo "  Starting MotionScript..."
echo "  Open http://localhost:5000 in your browser"
echo "  Press Ctrl+C to stop"
echo ""

"$VENV_DIR/bin/python" "$SCRIPT_DIR/app.py"
