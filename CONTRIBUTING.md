# Contributing to fftpeg

## Project Overview

**fftpeg** is a dual-mode ffmpeg TUI/CLI tool written in Python.

- **Language**: Python 3.9+
- **Main Dependencies**: textual, ffmpeg-python, yt-dlp, pymediainfo
- **License**: Apache 2.0
- **Repository**: https://github.com/Jos-few43/fftpeg

## Architecture

### Core Components

```
src/
├── main.py                 # Entry point - handles CLI arg parsing, routes to TUI or CLI mode
├── app.py                  # Main Textual app class for TUI mode
├── cli.py                  # CLI command implementations (pull, convert, compress, etc.)
├── screens/                # Textual UI screens
│   ├── main_menu.py        # File browser with video list
│   └── pull_screen.py      # Pull/download URL interface
├── operations/             # Video operation logic (future: convert, compress, trim, etc.)
├── utils/
│   ├── downloader.py       # VideoDownloader class - yt-dlp integration
│   ├── database.py         # Database class - SQLite operations
│   ├── symlink_manager.py  # SymlinkManager class - file organization
│   └── metadata.py         # Video metadata extraction (future)
└── config/
    └── settings.py         # Config class - manages ~/.config/fftpeg/config.json
```

### Data Flow

**TUI Mode**:
```
fftpeg [path] → main.py → app.py (FFTpegApp) → screens/main_menu.py → user selects operation
```

**CLI Mode**:
```
fftpeg <command> [args] → main.py → cli.py (CLI class) → operation methods
```

**Pull/Download Flow**:
```
URL input → VideoDownloader.download()
  ├─ Check database for existing URL
  ├─ Download with yt-dlp to downloads/
  ├─ Calculate file hash
  ├─ Add to database (downloads table)
  ├─ Extract metadata
  └─ SymlinkManager.organize_file()
      ├─ by-source/{platform}/
      ├─ by-tag/{tag}/ (for each tag)
      └─ by-date/{YYYY-MM}/
```

### Database Schema

**Location**: `~/.config/fftpeg/fftpeg.db`

**Tables**:
- `downloads` - Downloaded files (url, source, filepath, hash, metadata)
- `tags` - Tag definitions (id, name)
- `file_tags` - Many-to-many relationship (file_id, tag_id)
- `auto_tag_rules` - Automatic tagging rules (pattern, tag_id)

### Configuration

**Location**: `~/.config/fftpeg/config.json`

**Structure**:
```json
{
  "download_path": "~/Videos/fftpeg/downloads",
  "organize_by_source": true,
  "organize_by_tag": true,
  "organize_by_date": true,
  "source_formats": {
    "youtube": {"format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]"},
    "twitter": {"format": "best"},
    ...
  },
  "auto_tag_rules": {
    "youtube.com": ["youtube"],
    "twitter.com": ["twitter"],
    ...
  }
}
```

## Development Workflow

### Branch Strategy

- **`master`** - Stable, production-ready code. Only merge tested features.
- **`dev`** - Active development branch. All feature branches merge here first.
- **`feature/*`** - Feature branches. Branch from `dev`, merge back to `dev`.

### Workflow Steps

```bash
# 1. Start new feature
git checkout dev
git pull
git checkout -b feature/your-feature-name

# 2. Make changes
# ... edit files ...

# 3. Test locally
./fftpeg.sh           # Test TUI mode
source venv/bin/activate
python -m pytest      # Run tests (when available)

# 4. Commit
git add .
git commit -m "feat: Description of feature"

# 5. Push and create PR to dev
git push -u origin feature/your-feature-name
gh pr create --base dev --title "Add feature: description"

# 6. After PR approved and merged to dev, test on dev
git checkout dev
git pull

# 7. When ready for release, merge dev → master
gh pr create --base master --head dev --title "Release: v0.x.0"
```

### Commit Message Convention

Use conventional commits for clarity:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

Example: `feat: Add batch conversion support`

## Adding New Features

### Adding a New CLI Command

1. **Add argument parser** in `src/main.py`:
```python
# Add subcommand
new_parser = subparsers.add_parser('newcommand', help='Description')
new_parser.add_argument('input', help='Input file')
new_parser.add_argument('-o', '--output', help='Output file')
```

2. **Add command check** in main.py line 72:
```python
if len(sys.argv) > 1 and sys.argv[1] in ['pull', 'convert', ..., 'newcommand', ...]:
```

3. **Implement method** in `src/cli.py`:
```python
def newcommand(self, input_file: str, output_file: Optional[str] = None) -> int:
    """New command implementation."""
    # Implementation here
    return 0  # Success
```

4. **Add handler** in main.py:
```python
elif args.command == 'newcommand':
    return cli.newcommand(args.input, args.output)
```

### Adding a New TUI Screen

1. **Create screen file** in `src/screens/new_screen.py`:
```python
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Header, Footer, Static

class NewScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("New Screen Content")
        yield Footer()
```

2. **Add keybinding** in `src/screens/main_menu.py`:
```python
BINDINGS = [
    ...
    Binding("n", "new_screen", "New Screen", show=True),
]

def action_new_screen(self) -> None:
    from .new_screen import NewScreen
    self.app.push_screen(NewScreen())
```

### Adding a New Video Operation

1. **Create operation file** in `src/operations/new_operation.py`:
```python
import ffmpeg
from pathlib import Path

class NewOperation:
    def execute(self, input_path: Path, output_path: Path, **kwargs):
        stream = ffmpeg.input(str(input_path))
        # ... operation logic ...
        ffmpeg.run(stream)
```

2. **Add to CLI** in `src/cli.py` (follow existing patterns)

3. **Add to TUI** in appropriate screen (follow existing patterns)

## Testing

### Manual Testing Checklist

Before merging to `dev`:

- [ ] TUI launches: `./fftpeg.sh`
- [ ] TUI with path: `./fftpeg.sh ~/Videos`
- [ ] CLI help: `fftpeg --help`
- [ ] CLI command: `fftpeg pull --preview <url>`
- [ ] No Python errors or tracebacks
- [ ] Files created in correct locations
- [ ] Symlinks working correctly

### Test with Sample Data

```bash
# Test pull
fftpeg pull --preview https://www.youtube.com/watch?v=jNQXAC9IVRw

# Test compress
fftpeg compress test.mp4 --crf 28

# Test audio extraction
fftpeg extract-audio test.mp4 -f mp3
```

## Code Style

### Python Conventions

- Follow PEP 8
- Use type hints where practical
- Docstrings for all public methods
- Keep functions focused and small
- Use pathlib.Path for file operations

### Error Handling

Always handle errors gracefully:

```python
try:
    result = operation()
except ffmpeg.Error as e:
    print(f"✗ FFmpeg error: {e.stderr.decode()}", file=sys.stderr)
    return 1
except Exception as e:
    print(f"✗ Error: {str(e)}", file=sys.stderr)
    return 1
```

### CLI Output Format

Use consistent emoji and formatting:

```python
print(f"🎬 Convert: {input_path.name} → {output_path.name}")
print(f"✓ Conversion complete!")
print(f"✗ Error: {message}", file=sys.stderr)
```

## File Organization Standards

### Downloads Organization

All downloaded files follow this structure:

```
~/Videos/fftpeg/
├── downloads/              # Real files (single source of truth)
│   └── video.mp4
├── by-source/              # Symlinks organized by platform
│   ├── youtube/
│   │   └── video.mp4 → ../../downloads/video.mp4
│   └── twitter/
├── by-tag/                 # Symlinks organized by tags
│   ├── tutorial/
│   │   └── video.mp4 → ../../downloads/video.mp4
│   └── music/
└── by-date/                # Symlinks organized by month
    └── 2025-12/
        └── video.mp4 → ../../downloads/video.mp4
```

**Important**: Always use relative symlinks for portability.

## Common Patterns

### Reading Config

```python
from src.config.settings import Config

config = Config()
org_paths = config.get_organization_paths()
download_path = org_paths['downloads']
```

### Database Operations

```python
from src.utils.database import Database

db = Database()
existing = db.check_url_exists(url)
file_id = db.add_download(url, source, filepath, metadata)
db.add_tag_to_file(file_id, "tutorial")
```

### Creating Symlinks

```python
from src.utils.symlink_manager import SymlinkManager

symlink_mgr = SymlinkManager(base_path)
symlink_mgr.organize_file(filepath, source="youtube", tags=["tutorial"], date=datetime.now())
```

### FFmpeg Operations

```python
import ffmpeg

stream = ffmpeg.input(str(input_path))
stream = ffmpeg.output(stream, str(output_path), vcodec='libx264', crf=23)
cmd = ' '.join(ffmpeg.compile(stream))
print(f"▶ Running: ffmpeg {cmd.split('ffmpeg')[1]}")
ffmpeg.run(stream, overwrite_output=True)
```

## Future Roadmap

Features planned but not yet implemented:

- [ ] TUI implementations of convert/compress/audio/trim operations
- [ ] Batch operations (process multiple files)
- [ ] Preset system (save common configurations)
- [ ] Advanced metadata extraction and display
- [ ] File renaming with pattern support
- [ ] Deduplication with hash comparison
- [ ] Plugin system for custom operations
- [ ] Video preview in terminal (using sixel/kitty graphics)

## Dependencies

### Core Dependencies

- **textual** - TUI framework
- **ffmpeg-python** - FFmpeg Python wrapper
- **yt-dlp** - Video downloader
- **pymediainfo** - Metadata extraction
- **rich** - Terminal formatting

### System Requirements

- Python 3.9+
- ffmpeg (system binary)
- libmediainfo (system library)

### Installation

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## AI Assistant Guidelines

When helping with this project:

1. **Always read existing code** before suggesting changes
2. **Follow established patterns** (see Common Patterns section)
3. **Test changes** before committing (see Manual Testing Checklist)
4. **Update README.md** if adding user-facing features
5. **Use conventional commits** for commit messages
6. **Work on feature branches**, not directly on dev/master
7. **Preserve file organization** (downloads/, by-source/, by-tag/, by-date/)
8. **Handle errors gracefully** with user-friendly messages
9. **Show ffmpeg commands** before executing (transparency principle)
10. **Keep it simple** - avoid over-engineering

## Questions or Issues?

For bugs, feature requests, or questions:
- Open an issue: https://github.com/Jos-few43/fftpeg/issues
- Follow issue template (when available)
- Include error messages and steps to reproduce

## License

Apache 2.0 - See LICENSE file for details.
