# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Modern TUI and CLI tool for ffmpeg operations. Provides an interactive terminal interface for browsing/managing videos and a command-line interface for scripting video conversions, compression, extraction, and trimming.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.9+ |
| TUI | Textual |
| Formatting | Rich |
| Video | ffmpeg, ffmpeg-python |
| Downloads | yt-dlp |
| Metadata | pymediainfo |

## Project Structure

```
fftpeg/
├── src/
│   ├── main.py           # Entry point
│   ├── app.py            # Main Textual TUI application
│   ├── cli.py            # CLI command handler
│   ├── operations/       # Video operations (convert, compress, extract, trim)
│   ├── screens/          # Interactive TUI screens
│   ├── components/       # Reusable UI widgets
│   └── utils/            # FFmpeg wrapper, database, symlink manager
├── requirements.txt
├── setup.py
└── fftpeg.sh             # Launch script
```

## Key Commands

```bash
./fftpeg.sh                                    # Launch TUI
fftpeg pull <url>                              # Download video (YouTube, Twitter, etc.)
fftpeg compress video.mp4 --crf 23             # Compress with quality setting
fftpeg extract-audio video.mp4 -f mp3          # Extract audio
fftpeg convert input.avi output.mp4            # Convert format
fftpeg trim video.mp4 -s 00:00:10 -e 00:01:00 # Trim video
```

## Things to Avoid

- Don't process videos without ffmpeg installed
- Don't hardcode `/home/yish` — use `$HOME` or `/var/home/yish`
