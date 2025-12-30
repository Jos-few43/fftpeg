#!/usr/bin/env python3
"""Main entry point for fftpeg."""

import sys
import argparse
from pathlib import Path
from app import FFTpegApp


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="fftpeg - A modern Terminal User Interface for ffmpeg operations"
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Directory to browse for video files (default: current directory)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="fftpeg 0.1.0",
    )

    args = parser.parse_args()

    # Validate path
    path = Path(args.path).expanduser().resolve()
    if not path.exists():
        print(f"Error: Path '{path}' does not exist", file=sys.stderr)
        sys.exit(1)

    if not path.is_dir():
        print(f"Error: Path '{path}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # Run the TUI app
    app = FFTpegApp(start_path=path)
    app.run()


if __name__ == "__main__":
    main()
