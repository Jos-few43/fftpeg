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

# Activate virtual environment
VENV_DIR=$(< "$HOME/.config/fftpeg/config.txt")
source "$VENV_DIR/venv/bin/activate"

# Add project root to PYTHONPATH so src.main can be found
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Run fftpeg with any arguments passed to this script
# Default to current directory if no path provided
if [ $# -eq 0 ]; then
    python -m src.main .
else
    python -m src.main "$@"
fi
