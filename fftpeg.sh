#!/bin/bash
# Quick launch script for fftpeg

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Activate virtual environment
source "$SCRIPT_DIR/venv/bin/activate"

# Run fftpeg with any arguments passed to this script
# Default to current directory if no path provided
if [ $# -eq 0 ]; then
    python -m src.main .
else
    python -m src.main "$@"
fi
