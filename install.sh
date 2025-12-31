#!/bin/bash
# Install fftpeg globally (adds symlink to ~/.local/bin)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"

# Create install directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Create symlink
ln -sf "$SCRIPT_DIR/fftpeg.sh" "$INSTALL_DIR/fftpeg"

echo "✓ fftpeg installed to $INSTALL_DIR/fftpeg"
echo ""
echo "Make sure $INSTALL_DIR is in your PATH."
echo "Add this to your ~/.bashrc or ~/.zshrc if needed:"
echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
echo ""
echo "Now you can run 'fftpeg' from anywhere!"
