#!/bin/bash
# Quick launch script for fftpeg

# Get the directory where this script is actually located (follow symlinks)
SCRIPT_PATH="${BASH_SOURCE[0]}"
# Resolve symlinks
while [ -L "$SCRIPT_PATH" ]; do
    SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" && pwd)"
    SCRIPT_PATH="$(readlink "$SCRIPT_PATH")"
    [[ $SCRIPT_PATH != /* ]] && SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_PATH"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SCRIPT_PATH")" && pwd)"

# Save current directory
ORIGINAL_DIR="$(pwd)"

# Change to project directory
cd "$SCRIPT_DIR"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run fftpeg with any arguments passed to this script
# Default to current directory if no path provided
if [ $# -eq 0 ]; then
    python -m src.main "$ORIGINAL_DIR"
else
    python -m src.main "$@"
fi
