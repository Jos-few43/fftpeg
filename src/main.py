#!/usr/bin/env python3
"""Main entry point for fftpeg."""

import sys
import argparse
from pathlib import Path
from .app import FFTpegApp
from .cli import CLI


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(
        description="fftpeg - A modern Terminal User Interface and CLI for ffmpeg operations",
        epilog="Run without arguments to launch the TUI"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="fftpeg 0.1.0",
    )

    # Add subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Pull command
    pull_parser = subparsers.add_parser('pull', help='Download video from URL')
    pull_parser.add_argument('url', help='Video URL (YouTube, Twitter, Instagram, etc.)')
    pull_parser.add_argument('-t', '--tags', help='Comma-separated tags (e.g., tutorial,archive)')
    pull_parser.add_argument('-p', '--preview', action='store_true',
                            help='Preview video info without downloading')

    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert video format')
    convert_parser.add_argument('input', help='Input video file')
    convert_parser.add_argument('output', help='Output video file')
    convert_parser.add_argument('-c', '--codec', help='Video codec (default: copy streams)')

    # Compress command
    compress_parser = subparsers.add_parser('compress', help='Compress video')
    compress_parser.add_argument('input', help='Input video file')
    compress_parser.add_argument('-o', '--output', help='Output file (default: input_compressed.ext)')
    compress_parser.add_argument('--crf', type=int, default=23,
                                help='CRF value 18-28 (lower=better quality, default: 23)')
    compress_parser.add_argument('--preset', default='medium',
                                choices=['ultrafast', 'fast', 'medium', 'slow', 'veryslow'],
                                help='Encoding preset (default: medium)')

    # Extract audio command
    audio_parser = subparsers.add_parser('extract-audio', help='Extract audio from video',
                                        aliases=['audio'])
    audio_parser.add_argument('input', help='Input video file')
    audio_parser.add_argument('-o', '--output', help='Output audio file (default: input.mp3)')
    audio_parser.add_argument('-f', '--format', default='mp3',
                             choices=['mp3', 'm4a', 'flac', 'wav'],
                             help='Audio format (default: mp3)')
    audio_parser.add_argument('-q', '--quality', default='320k',
                             help='Audio quality/bitrate (default: 320k)')

    # Trim command
    trim_parser = subparsers.add_parser('trim', help='Trim/cut video')
    trim_parser.add_argument('input', help='Input video file')
    trim_parser.add_argument('-o', '--output', help='Output file (default: input_trimmed.ext)')
    trim_parser.add_argument('-s', '--start', default='00:00:00',
                            help='Start time HH:MM:SS (default: 00:00:00)')
    trim_group = trim_parser.add_mutually_exclusive_group()
    trim_group.add_argument('-e', '--end', help='End time HH:MM:SS')
    trim_group.add_argument('-d', '--duration', help='Duration from start HH:MM:SS')

    # TUI mode (no subcommand)
    parser.add_argument(
        "path",
        nargs="?",
        help="Directory to browse (TUI mode only)",
    )

    args = parser.parse_args()

    # Handle commands
    if args.command:
        cli = CLI()

        if args.command == 'pull':
            return cli.pull(args.url, args.tags, args.preview)

        elif args.command == 'convert':
            return cli.convert(args.input, args.output, args.codec)

        elif args.command == 'compress':
            return cli.compress(args.input, args.output, args.crf, args.preset)

        elif args.command in ['extract-audio', 'audio']:
            return cli.extract_audio(args.input, args.output, args.format, args.quality)

        elif args.command == 'trim':
            return cli.trim(args.input, args.output, args.start, args.end, args.duration)

    # TUI mode (no command specified)
    else:
        path = Path(args.path or ".").expanduser().resolve()

        if not path.exists():
            print(f"Error: Path '{path}' does not exist", file=sys.stderr)
            sys.exit(1)

        if not path.is_dir():
            print(f"Error: Path '{path}' is not a directory", file=sys.stderr)
            sys.exit(1)

        # Run the TUI app
        app = FFTpegApp(start_path=path)
        app.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
