#!/bin/bash

VENV_DIR="$HOME/intel_agentbot/.venv"

# Create .venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "🔧 Creating virtual environment in $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment." >&2
        return 1 2>/dev/null || exit 1
    fi
    echo "✅ Virtual environment created."
else
    echo "✅ Virtual environment already exists."
fi

# Activate the environment
echo "⚡ Activating virtual environment..."
source "$VENV_DIR/bin/activate"


