#!/bin/bash
# ──────────────────────────────────────────────────────────────────────────────
# MotionScript – One-click setup
# Run this ONCE before using the app.
# ──────────────────────────────────────────────────────────────────────────────

set -e

echo ""
echo "  ┌─────────────────────────────────────┐"
echo "  │   MotionScript – Setup              │"
echo "  └─────────────────────────────────────┘"
echo ""

# ── Detect OS ─────────────────────────────────────────────────────────────────
OS="$(uname -s)"

# ── 1. System dependencies ────────────────────────────────────────────────────
echo "[1/3] Checking system dependencies..."

# On macOS, ensure Homebrew is available
if [[ "$OS" == "Darwin" ]] && ! command -v brew &> /dev/null; then
    echo "  → Homebrew not found. Installing Homebrew first..."
    echo "    (You may be prompted for your password)"
    echo ""
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add brew to PATH for this session (Apple Silicon vs Intel)
    if [ -f "/opt/homebrew/bin/brew" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        echo "  → Adding Homebrew to your shell profile..."
        echo '' >> "$HOME/.zprofile"
        echo '# Homebrew' >> "$HOME/.zprofile"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
    elif [ -f "/usr/local/bin/brew" ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    echo "  ✓ Homebrew installed"
fi

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "  → Installing ffmpeg..."
    if [[ "$OS" == "Darwin" ]]; then
        brew install ffmpeg
    elif [[ "$OS" == "Linux" ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg libcairo2-dev pkg-config python3-dev
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y ffmpeg cairo-devel pkg-config python3-devel
        elif command -v pacman &> /dev/null; then
            sudo pacman -S --noconfirm ffmpeg cairo pkg-config python
        else
            echo "  ERROR: Could not detect package manager. Install ffmpeg manually."
            exit 1
        fi
    fi
else
    echo "  ✓ ffmpeg found"
fi

# Check cairo headers (needed for pycairo compilation)
if [[ "$OS" == "Linux" ]]; then
    if ! pkg-config --exists cairo 2>/dev/null; then
        echo "  → Installing cairo development headers..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y -qq libcairo2-dev pkg-config python3-dev
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y cairo-devel pkg-config python3-devel
        fi
    else
        echo "  ✓ cairo headers found"
    fi
elif [[ "$OS" == "Darwin" ]]; then
    if ! pkg-config --exists cairo 2>/dev/null; then
        echo "  → Installing cairo via Homebrew..."
        brew install cairo pkg-config
    else
        echo "  ✓ cairo found"
    fi
fi

# ── 2. Python virtual environment ────────────────────────────────────────────
echo ""
echo "[2/3] Setting up Python virtual environment..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "  ✓ Virtual environment created"
else
    echo "  ✓ Virtual environment already exists"
fi

# ── 3. Install Python packages ───────────────────────────────────────────────
echo ""
echo "[3/3] Installing Python packages..."

"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$SCRIPT_DIR/requirements.txt" -q

echo "  ✓ All packages installed"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "  ┌─────────────────────────────────────┐"
echo "  │   Setup complete!                   │"
echo "  │                                     │"
echo "  │   To run:  ./run.sh                 │"
echo "  │   Or:      python3 run.py           │"
echo "  └─────────────────────────────────────┘"
echo ""
