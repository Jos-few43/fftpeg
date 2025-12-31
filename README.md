# fftpeg

> A modern Terminal User Interface (TUI) and CLI for ffmpeg operations

**fftpeg** (pronounced "eff-eff-tee-peg") is a powerful dual-mode tool that makes video processing with ffmpeg accessible and visual. Use the interactive TUI for browsing and exploring, or the CLI for scripting and quick operations. Built for the terminal, designed for efficiency.

## Features

### 🎬 Smart Pull System (NEW!)
- **Download from URLs** - YouTube, Twitter, Instagram, Vimeo, TikTok, Twitch, and more
- **Auto-tagging** - Automatically tag downloads based on source platform
- **Smart Organization** - Symlink-based file organization (by-source, by-tag, by-date)
- **Duplicate Detection** - Hash-based checking prevents re-downloading
- **Custom Tags** - Add your own tags for advanced organization
- **Preview Info** - View video metadata before downloading

### 🎞️ Video Operations
- **Interactive File Browser** - Navigate your video files with ease
- **Common Operations** - Convert, compress, extract audio, trim videos (coming soon)
- **Smart Metadata** - View codec, resolution, bitrate, duration at a glance
- **File Management** - Rename files and deduplicate your collection
- **Command Preview** - See the exact ffmpeg command before execution
- **Progress Tracking** - Real-time progress bars during conversions
- **Keyboard-First** - All operations accessible via keyboard shortcuts

## Installation

### Prerequisites

- Python 3.9 or higher
- ffmpeg installed on your system
- MediaInfo library (for metadata extraction)

#### Install system dependencies:

**Arch Linux:**
```bash
sudo pacman -S ffmpeg libmediainfo
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg libmediainfo0v5
```

**macOS:**
```bash
brew install ffmpeg media-info
```

### Install fftpeg

```bash
# Clone the repository
git clone https://github.com/Jos-few43/fftpeg.git
cd fftpeg

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Quick run (local)
./fftpeg.sh

# Or install globally (recommended)
./install.sh
# Then run from anywhere:
fftpeg ~/Videos
```

## Quick Start

1. Launch fftpeg in a directory with video files:
   ```bash
   cd ~/Videos
   ./fftpeg.sh
   # Or if installed globally:
   fftpeg
   ```

2. Use arrow keys to navigate files
3. Press operation shortcuts:
   - `U` - **Pull from URL** (Download videos!)
   - `C` - Convert format
   - `P` - Compress video
   - `A` - Extract/convert audio
   - `T` - Trim video
   - `R` - Rename files
   - `D` - Deduplicate
   - `Q` - Quit

4. Follow the prompts to configure your operation
5. Review the ffmpeg command preview
6. Confirm to execute

### Pull Feature Example

```bash
# Launch fftpeg
./fftpeg.sh

# Press 'U' for Pull
# Paste URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
# Add tags (optional): music, favorites
# Press Download

# File automatically organized:
# ~/Videos/fftpeg/downloads/Never_Gonna_Give_You_Up.mp4  (real file)
# ~/Videos/fftpeg/by-source/youtube/ → symlink
# ~/Videos/fftpeg/by-tag/music/ → symlink
# ~/Videos/fftpeg/by-tag/favorites/ → symlink
# ~/Videos/fftpeg/by-date/2025-12/ → symlink
```

## CLI Usage

fftpeg also works as a powerful command-line tool for scripting and quick operations:

### Pull Videos
```bash
# Download video
fftpeg pull https://youtube.com/watch?v=...

# Add custom tags
fftpeg pull https://youtube.com/watch?v=... -t "tutorial,favorite"

# Preview info without downloading
fftpeg pull https://youtube.com/watch?v=... --preview
```

### Compress Videos
```bash
# Compress with defaults (CRF 23, medium preset)
fftpeg compress video.mp4

# Customize quality and speed
fftpeg compress video.mp4 --crf 28 --preset fast -o output.mp4

# Higher quality, slower encoding
fftpeg compress video.mp4 --crf 18 --preset slow
```

### Extract Audio
```bash
# Extract as MP3 (default 320k)
fftpeg extract-audio video.mp4

# Specify format and quality
fftpeg extract-audio video.mp4 -f m4a -q 192k

# Extract as FLAC (lossless)
fftpeg audio video.mp4 -f flac
```

### Convert Formats
```bash
# Fast container change (stream copy)
fftpeg convert input.avi output.mp4

# Re-encode with specific codec
fftpeg convert input.mp4 output.mkv -c libx265
```

### Trim Videos
```bash
# Trim from 10s to 60s
fftpeg trim video.mp4 -s 00:00:10 -e 00:01:00

# Trim 30 seconds starting at 1 minute
fftpeg trim video.mp4 -s 00:01:00 -d 00:00:30 -o clip.mp4
```

### Get Help
```bash
# Show all commands
fftpeg --help

# Show help for specific command
fftpeg pull --help
fftpeg compress --help
```

## Operations

### Pull from URL
Download videos from major platforms with smart organization:
- **Supported Platforms**: YouTube, Twitter/X, Instagram, Vimeo, TikTok, Twitch, Reddit, and more (powered by yt-dlp)
- **Auto-tagging**: Files automatically tagged with source platform
- **Custom Tags**: Add your own tags (tutorial, archive, music, etc.)
- **Smart Storage**: One physical file, organized via symlinks in multiple locations
- **Duplicate Detection**: Checks URL and file hash to prevent re-downloads
- **Preview Mode**: View video info (title, duration, uploader) before downloading

**File Organization Structure:**
```
~/Videos/fftpeg/
├── downloads/          # Real files stored here
├── by-source/         # youtube/, twitter/, instagram/, etc.
├── by-tag/            # tutorial/, music/, archive/, etc.
└── by-date/           # 2025-12/, 2025-11/, etc.
```

### Convert Format
Change video container format (MP4, MKV, WebM, AVI, etc.) while preserving or transcoding streams. **Available in CLI mode.**

### Compress Video
Reduce file size with configurable quality settings (CRF 18-28) and encoding presets. **Available in CLI mode.**

### Extract Audio
Pull audio tracks from video files or convert between audio formats (MP3, M4A, FLAC, WAV). **Available in CLI mode.**

### Trim Video
Cut portions of video by specifying start and end times or duration. **Available in CLI mode.**

### Rename Files
Smart renaming based on metadata patterns or bulk operations. *(Coming soon)*

### Deduplicate
Find and manage duplicate video files using hash-based detection with SQLite database tracking. *(Coming soon)*

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑`/`↓` | Navigate file list |
| `Enter` | Select file/confirm |
| **`U`** | **Pull from URL** ⭐ |
| `C` | Convert format |
| `P` | Compress video |
| `A` | Audio operations |
| `T` | Trim video |
| `R` | Rename files |
| `D` | Deduplicate |
| `S` | Settings/Presets |
| `F1` | Help |
| `Q`/`Esc` | Quit/Back |

## Development

### Project Structure

```
fftpeg/
├── src/
│   ├── main.py              # Entry point
│   ├── app.py               # Main Textual app
│   ├── screens/             # UI screens
│   ├── components/          # Reusable widgets
│   ├── operations/          # Video operations
│   ├── utils/               # FFmpeg wrapper, metadata, database
│   └── config/              # Presets and configuration
├── tests/                   # Unit tests
├── docs/                    # Documentation
└── requirements.txt         # Dependencies
```

### Running Tests

```bash
pytest tests/
```

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual) - amazing TUI framework
- Powered by [FFmpeg](https://ffmpeg.org/) - the Swiss Army knife of video processing
- Inspired by the open-source community's dedication to accessible, powerful tools

## Roadmap

- [ ] Core TUI framework with file browser
- [ ] Basic operations (convert, compress, audio, trim)
- [ ] Metadata extraction and display
- [ ] File management (rename, dedupe)
- [ ] Preset system for common tasks
- [ ] Batch operations
- [ ] Plugin system for custom operations
- [ ] Video preview in terminal

## Support

If you find this project useful, please consider starring it on GitHub!

For bugs and feature requests, please [open an issue](https://github.com/yourusername/fftpeg/issues).

---

Made with ❤️ for the terminal
