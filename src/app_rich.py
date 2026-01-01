#!/usr/bin/env python3
"""
fftpeg Rich TUI - File browser and ffmpeg operations
Follows the ai-hub design pattern using Rich library
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Tuple
from datetime import datetime
import ffmpeg

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich import box
    from rich.columns import Columns
    import readchar
except ImportError as e:
    print(f"Error: Missing library. Installing...")
    subprocess.run([sys.executable, "-m", "pip", "install", "rich", "readchar"], check=True)
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich import box
    from rich.columns import Columns
    import readchar

# Import existing utilities
from .utils.theme_detector import get_theme, get_theme_colors, get_available_themes

console = Console()

# File type filters
FILTER_TYPES = {
    "all": {"label": "All Files", "exts": set()},
    "video": {"label": "Video Files", "exts": {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".m4v"}},
    "audio": {"label": "Audio Files", "exts": {".mp3", ".m4a", ".flac", ".wav", ".ogg", ".aac"}},
    "image": {"label": "Image Files", "exts": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}},
}

@dataclass
class FileItem:
    """Represents a file or directory in the browser."""
    path: Path
    is_dir: bool
    size: int
    modified: datetime

    @property
    def size_str(self) -> str:
        """Human-readable file size."""
        if self.is_dir:
            return "<DIR>"

        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    @property
    def modified_str(self) -> str:
        """Human-readable modification time."""
        return self.modified.strftime("%Y-%m-%d %H:%M")


class FFTpegRichApp:
    """Main application using Rich for UI."""

    def __init__(self, start_path: Path):
        self.start_path = start_path
        self.current_path = start_path
        self.selected_index = 0
        self.show_hidden = False
        self.current_filter = "all"
        self.filter_enabled = True

        # Batch processing
        self.marked_files = set()  # Set of Path objects
        self.batch_url_queue = []  # List of URLs to download

        # Theme setup
        theme_name = get_theme()
        theme_colors = get_theme_colors(theme_name)
        self.theme = {
            "primary": theme_colors["primary"],
            "secondary": theme_colors["secondary"],
            "accent": theme_colors["accent"],
            "success": theme_colors["success"],
            "warning": theme_colors["warning"],
            "error": theme_colors["error"],
            "muted": theme_colors["text-muted"],
            "border": theme_colors["primary"],
        }
        self.theme_name = theme_name

    def get_file_list(self) -> List[FileItem]:
        """Get list of files in current directory based on filters."""
        files = []

        try:
            for item in self.current_path.iterdir():
                # Skip hidden files if not showing them
                if not self.show_hidden and item.name.startswith('.'):
                    continue

                # Apply file type filter (only to files, not directories)
                if self.filter_enabled and self.current_filter != "all" and not item.is_dir():
                    filter_exts = FILTER_TYPES[self.current_filter]["exts"]
                    if item.suffix.lower() not in filter_exts:
                        continue

                # Get file stats
                try:
                    stat = item.stat()
                    files.append(FileItem(
                        path=item,
                        is_dir=item.is_dir(),
                        size=stat.st_size,
                        modified=datetime.fromtimestamp(stat.st_mtime)
                    ))
                except (OSError, PermissionError):
                    # Skip files we can't stat
                    continue
        except PermissionError:
            pass

        # Sort: directories first, then by name
        files.sort(key=lambda f: (not f.is_dir, f.path.name.lower()))

        return files

    def display_file_browser(self, files: List[FileItem], status_msg: str = ""):
        """Render the file browser interface."""
        console.clear()

        # Get terminal size
        terminal_height = console.size.height
        terminal_width = console.size.width

        # Calculate available space for file table
        # Header (4 lines) + Status (3 lines) + Footer (3 lines) = 10 lines reserved
        reserved_lines = 10
        max_table_rows = max(5, terminal_height - reserved_lines)

        # Header
        header_text = f"[bold {self.theme['primary']}]🎬 fftpeg - Terminal FFmpeg[/]"
        header_path = f"[{self.theme['muted']}]{self.current_path}[/]"
        console.print(Panel.fit(
            f"{header_text}\n{header_path}",
            style=self.theme['primary'],
            border_style=self.theme['border']
        ))
        console.print()

        # Build all items (including ..)
        all_items = []
        offset = 0
        if self.current_path != self.current_path.parent:
            all_items.append(("..", None))  # Parent directory marker
            offset = 1

        for file in files:
            all_items.append((file.path.name, file))

        total_items = len(all_items)

        # Calculate visible range (scrolling window)
        # Center the selection in the visible area when possible
        half_window = max_table_rows // 2

        if total_items <= max_table_rows:
            # All items fit on screen
            start_idx = 0
            end_idx = total_items
        else:
            # Need scrolling - center selected item
            start_idx = max(0, self.selected_index - half_window)
            end_idx = min(total_items, start_idx + max_table_rows)

            # Adjust if we hit the end
            if end_idx == total_items:
                start_idx = max(0, total_items - max_table_rows)

        visible_items = all_items[start_idx:end_idx]

        # File table
        table = Table(
            box=box.ROUNDED,
            border_style=self.theme['border'],
            show_header=True,
            header_style=f"bold {self.theme['accent']}",
            width=terminal_width - 4  # Account for padding
        )
        table.add_column("Name", style="white", no_wrap=False, overflow="ellipsis")
        table.add_column("Size", justify="right", style=self.theme['muted'], width=10)
        table.add_column("Modified", style=self.theme['muted'], width=16)

        # Add visible items to table
        for idx in range(start_idx, end_idx):
            name, file = all_items[idx]
            is_selected = idx == self.selected_index

            # Handle parent directory
            if name == "..":
                if is_selected:
                    table.add_row(
                        f"[bold {self.theme['success']}]▶ ..[/]",
                        "",
                        ""
                    )
                else:
                    table.add_row(f"[{self.theme['muted']}]  ..[/]", "", "")
                continue

            # Icon and name
            if file.is_dir:
                icon = "📁"
                name_style = self.theme['accent']
            elif file.path.suffix.lower() in FILTER_TYPES["video"]["exts"]:
                icon = "🎬"
                name_style = self.theme['primary']
            elif file.path.suffix.lower() in FILTER_TYPES["audio"]["exts"]:
                icon = "🎵"
                name_style = self.theme['success']
            elif file.path.suffix.lower() in FILTER_TYPES["image"]["exts"]:
                icon = "🖼️"
                name_style = self.theme['warning']
            else:
                icon = "📄"
                name_style = "white"

            # Check if file is marked for batch processing
            is_marked = file.path in self.marked_files
            mark_icon = "✓" if is_marked else " "

            display_name = f"{icon} {name}"

            if is_selected:
                if is_marked:
                    table.add_row(
                        f"[bold {self.theme['success']}]▶[{self.theme['accent']}]{mark_icon}[/] {display_name}[/]",
                        f"[bold]{file.size_str}[/]",
                        f"[bold]{file.modified_str}[/]"
                    )
                else:
                    table.add_row(
                        f"[bold {self.theme['success']}]▶ {display_name}[/]",
                        f"[bold]{file.size_str}[/]",
                        f"[bold]{file.modified_str}[/]"
                    )
            else:
                if is_marked:
                    table.add_row(
                        f"[{self.theme['accent']}] {mark_icon}[/] [{self.theme['muted']}]{display_name}[/]",
                        file.size_str,
                        file.modified_str
                    )
                else:
                    table.add_row(
                        f"[{self.theme['muted']}]  {display_name}[/]",
                        file.size_str,
                        file.modified_str
                    )

        console.print(table)
        console.print()

        # Status line with scroll indicator and marked files
        filter_status = f"Filter: {FILTER_TYPES[self.current_filter]['label']}" if self.filter_enabled else "Filter: Off"
        hidden_status = "Hidden: On" if self.show_hidden else "Hidden: Off"

        # Show scroll position if there are more items than visible
        if total_items > max_table_rows:
            scroll_info = f"{self.selected_index + 1}/{total_items}"
        else:
            scroll_info = f"{total_items} items"

        # Show marked files count
        marked_count = len(self.marked_files)
        if marked_count > 0:
            marked_status = f"[{self.theme['accent']}]Marked: {marked_count}[/]"
        else:
            marked_status = ""

        # Show batch queue count
        queue_count = len(self.batch_url_queue)
        if queue_count > 0:
            queue_status = f"[{self.theme['primary']}]Queue: {queue_count}[/]"
        else:
            queue_status = ""

        status_parts = [filter_status, hidden_status, scroll_info]
        if marked_status:
            status_parts.append(marked_status)
        if queue_status:
            status_parts.append(queue_status)

        console.print(f"[{self.theme['muted']}]{' • '.join(status_parts)}[/]")

        if status_msg:
            console.print(f"[{self.theme['warning']}]{status_msg}[/]")

        console.print()

        # Help footer - split into multiple lines for readability
        console.print(
            f"[{self.theme['muted']}]"
            f"[{self.theme['primary']}]↑↓/jk[/] nav • "
            f"[{self.theme['primary']}]PgUp/PgDn[/] page • "
            f"[{self.theme['primary']}]g/G[/] top/bot • "
            f"[{self.theme['primary']}]Space[/]=Mark • "
            f"[{self.theme['accent']}]V[/]=MarkAll • "
            f"[{self.theme['accent']}]Ctrl+U[/]=Unmark • "
            f"[{self.theme['warning']}]B[/]=Batch • "
            f"[{self.theme['warning']}]Q[/]=Queue\n"
            f"[{self.theme['warning']}]U[/]=Pull • "
            f"[{self.theme['warning']}]C[/]=Conv • "
            f"[{self.theme['warning']}]P[/]=Comp • "
            f"[{self.theme['success']}]![/]=Hi • "
            f"[{self.theme['success']}]@[/]=Good • "
            f"[{self.theme['success']}]#[/]=Med • "
            f"[{self.theme['warning']}]A[/]=Audio • "
            f"[{self.theme['warning']}]T[/]=Trim • "
            f"[{self.theme['warning']}]M[/]=Move • "
            f"[{self.theme['error']}]Del[/]=Del\n"
            f"[{self.theme['warning']}]I[/]=Import • "
            f"[{self.theme['warning']}]N[/]=Rename • "
            f"[{self.theme['warning']}]F[/]=Filter • "
            f"[{self.theme['warning']}]H[/]=Hidden • "
            f"[{self.theme['warning']}]R[/]=Refresh • "
            f"[{self.theme['warning']}]O[/]=Options"
            f"[/]"
        )

    def cycle_filter(self):
        """Cycle through file type filters."""
        filters = list(FILTER_TYPES.keys())
        current_idx = filters.index(self.current_filter)
        next_idx = (current_idx + 1) % len(filters)
        self.current_filter = filters[next_idx]
        self.selected_index = 0  # Reset selection when filter changes

    def toggle_filter(self):
        """Toggle filter on/off."""
        self.filter_enabled = not self.filter_enabled
        self.selected_index = 0

    def toggle_hidden(self):
        """Toggle showing hidden files."""
        self.show_hidden = not self.show_hidden
        self.selected_index = 0

    def navigate_up(self, files: List[FileItem], amount: int = 1):
        """Navigate up in the file list."""
        max_idx = len(files)
        if self.current_path != self.current_path.parent:
            max_idx += 1  # Account for ".." entry

        if max_idx > 0:
            self.selected_index = (self.selected_index - amount) % max_idx

    def navigate_down(self, files: List[FileItem], amount: int = 1):
        """Navigate down in the file list."""
        max_idx = len(files)
        if self.current_path != self.current_path.parent:
            max_idx += 1  # Account for ".." entry

        if max_idx > 0:
            self.selected_index = (self.selected_index + amount) % max_idx

    def page_up(self, files: List[FileItem]):
        """Jump up by one page."""
        terminal_height = console.size.height
        reserved_lines = 10
        max_table_rows = max(5, terminal_height - reserved_lines)
        self.navigate_up(files, max_table_rows)

    def page_down(self, files: List[FileItem]):
        """Jump down by one page."""
        terminal_height = console.size.height
        reserved_lines = 10
        max_table_rows = max(5, terminal_height - reserved_lines)
        self.navigate_down(files, max_table_rows)

    def home(self):
        """Jump to first item."""
        self.selected_index = 0

    def end(self, files: List[FileItem]):
        """Jump to last item."""
        max_idx = len(files)
        if self.current_path != self.current_path.parent:
            max_idx += 1
        if max_idx > 0:
            self.selected_index = max_idx - 1

    def select_item(self, files: List[FileItem]) -> bool:
        """Handle selecting an item (navigate into directory). Returns True if should continue."""
        offset = 1 if self.current_path != self.current_path.parent else 0

        # Handle ".." (parent directory)
        if self.selected_index == 0 and self.current_path != self.current_path.parent:
            self.current_path = self.current_path.parent
            self.selected_index = 0
            return True

        # Handle file/directory selection
        actual_idx = self.selected_index - offset
        if 0 <= actual_idx < len(files):
            selected_file = files[actual_idx]

            if selected_file.is_dir:
                # Navigate into directory
                self.current_path = selected_file.path
                self.selected_index = 0
            else:
                # File selected - show info
                console.print(f"\n[{self.theme['accent']}]Selected: {selected_file.path.name}[/]")
                console.print(f"[{self.theme['muted']}]Use action keys (C/P/A/T/M/Del) to perform operations[/]")

        return True

    def get_selected_file(self, files: List[FileItem]) -> Optional[FileItem]:
        """Get the currently selected file (not directory)."""
        offset = 1 if self.current_path != self.current_path.parent else 0
        actual_idx = self.selected_index - offset

        if 0 <= actual_idx < len(files):
            file = files[actual_idx]
            if not file.is_dir:
                return file

        return None

    def delete_file(self, file: FileItem) -> bool:
        """Delete a file with confirmation dialog."""
        console.print()
        console.print(Panel.fit(
            f"[bold {self.theme['error']}]⚠️  Delete File[/]\n\n"
            f"Are you sure you want to delete:\n"
            f"[bold]{file.path.name}[/]\n\n"
            f"[{self.theme['muted']}]Size: {file.size_str}[/]\n"
            f"[{self.theme['muted']}]Path: {file.path}[/]",
            border_style=self.theme['error']
        ))

        if Confirm.ask(f"[{self.theme['error']}]Delete this file?[/]", default=False):
            try:
                file.path.unlink()
                console.print(f"[{self.theme['success']}]✓ File deleted successfully[/]")
                console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
                readchar.readkey()
                return True
            except Exception as e:
                console.print(f"[{self.theme['error']}]✗ Error deleting file: {e}[/]")
                console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
                readchar.readkey()
                return False

        return False

    def move_file(self, file: FileItem) -> bool:
        """Move a file to a new location."""
        console.print()
        console.print(Panel.fit(
            f"[bold {self.theme['warning']}]Move File[/]\n\n"
            f"Moving: [bold]{file.path.name}[/]\n"
            f"[{self.theme['muted']}]Current: {file.path.parent}[/]",
            border_style=self.theme['warning']
        ))

        dest_str = Prompt.ask(
            f"[{self.theme['accent']}]Enter destination path[/]",
            default=str(file.path.parent)
        )

        if not dest_str:
            return False

        dest_path = Path(dest_str).expanduser().resolve()

        # If destination is a directory, keep the same filename
        if dest_path.is_dir():
            dest_path = dest_path / file.path.name

        # Check if destination exists
        if dest_path.exists():
            console.print(f"[{self.theme['error']}]✗ Destination already exists: {dest_path}[/]")
            return False

        # Confirm move
        console.print(f"\n[{self.theme['muted']}]From: {file.path}[/]")
        console.print(f"[{self.theme['muted']}]To:   {dest_path}[/]\n")

        if Confirm.ask(f"[{self.theme['warning']}]Confirm move?[/]", default=True):
            try:
                # Create parent directory if it doesn't exist
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Move the file
                shutil.move(str(file.path), str(dest_path))
                console.print(f"[{self.theme['success']}]✓ File moved successfully[/]")
                console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
                readchar.readkey()
                return True
            except Exception as e:
                console.print(f"[{self.theme['error']}]✗ Error moving file: {e}[/]")
                console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
                readchar.readkey()
                return False

        return False

    def import_file(self) -> bool:
        """Import a file from another location to the current directory."""
        console.print()
        console.print(Panel.fit(
            f"[bold {self.theme['accent']}]Import File[/]\n\n"
            f"Import a file to: [bold]{self.current_path}[/]",
            border_style=self.theme['accent']
        ))

        source_str = Prompt.ask(
            f"[{self.theme['accent']}]Enter path to file to import[/]"
        )

        if not source_str:
            return False

        source_path = Path(source_str).expanduser().resolve()

        if not source_path.exists():
            console.print(f"[{self.theme['error']}]✗ File not found: {source_path}[/]")
            return False

        if source_path.is_dir():
            console.print(f"[{self.theme['error']}]✗ Cannot import directories (use move instead)[/]")
            return False

        dest_path = self.current_path / source_path.name

        # Check if destination exists
        if dest_path.exists():
            if not Confirm.ask(
                f"[{self.theme['warning']}]File already exists. Overwrite?[/]",
                default=False
            ):
                return False

        # Show what will happen
        source_size = source_path.stat().st_size
        size_str = f"{source_size / (1024**2):.1f} MB" if source_size > 1024**2 else f"{source_size / 1024:.1f} KB"

        console.print(f"\n[{self.theme['muted']}]File: {source_path.name} ({size_str})[/]")
        console.print(f"[{self.theme['muted']}]From: {source_path.parent}[/]")
        console.print(f"[{self.theme['muted']}]To:   {dest_path.parent}[/]\n")

        if Confirm.ask(f"[{self.theme['accent']}]Copy file to current directory?[/]", default=True):
            try:
                shutil.copy2(str(source_path), str(dest_path))
                console.print(f"[{self.theme['success']}]✓ File imported successfully[/]")
                console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
                readchar.readkey()
                return True
            except Exception as e:
                console.print(f"[{self.theme['error']}]✗ Error importing file: {e}[/]")
                console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
                readchar.readkey()
                return False

        return False

    def rename_file(self, file: FileItem) -> bool:
        """Rename a file."""
        console.print()
        console.print(Panel.fit(
            f"[bold {self.theme['accent']}]Rename File[/]\n\n"
            f"Current name: [bold]{file.path.name}[/]",
            border_style=self.theme['accent']
        ))

        new_name = Prompt.ask(
            f"[{self.theme['accent']}]Enter new name[/]",
            default=file.path.name
        )

        if not new_name or new_name == file.path.name:
            return False

        new_path = file.path.parent / new_name

        if new_path.exists():
            console.print(f"[{self.theme['error']}]✗ A file with that name already exists[/]")
            return False

        try:
            file.path.rename(new_path)
            console.print(f"[{self.theme['success']}]✓ File renamed successfully[/]")
            console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
            readchar.readkey()
            return True
        except Exception as e:
            console.print(f"[{self.theme['error']}]✗ Error renaming file: {e}[/]")
            console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
            readchar.readkey()
            return False

    def pull_video(self) -> bool:
        """Download video from URL using yt-dlp."""
        console.print()
        console.print(Panel.fit(
            f"[bold {self.theme['primary']}]📥 Pull Video[/]\n\n"
            f"Download video from URL (YouTube, Twitter, etc.)",
            border_style=self.theme['primary']
        ))

        url = Prompt.ask(f"[{self.theme['accent']}]Enter video URL[/]")

        if not url:
            return False

        # Ask if user wants to preview first
        if Confirm.ask(f"[{self.theme['muted']}]Preview video info first?[/]", default=True):
            console.print(f"\n[{self.theme['muted']}]Fetching video information...[/]")

            try:
                import yt_dlp

                ydl_opts = {'quiet': True, 'no_warnings': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                    duration_min = int(info['duration'] // 60) if info.get('duration') else 0
                    duration_sec = int(info['duration'] % 60) if info.get('duration') else 0

                    console.print(f"\n[bold {self.theme['accent']}]Video Information:[/]")
                    console.print(f"  Title:    {info.get('title', 'Unknown')}")
                    console.print(f"  Uploader: {info.get('uploader', 'Unknown')}")
                    console.print(f"  Duration: {duration_min}:{duration_sec:02d}")

                    if not Confirm.ask(f"\n[{self.theme['accent']}]Download this video?[/]", default=True):
                        return False

            except Exception as e:
                console.print(f"[{self.theme['warning']}]⚠ Could not fetch video info: {e}[/]")
                if not Confirm.ask(f"[{self.theme['accent']}]Continue with download anyway?[/]", default=False):
                    return False

        # Download to current directory
        output_path = self.current_path / "%(title)s.%(ext)s"

        console.print(f"\n[{self.theme['accent']}]Downloading to: {self.current_path}[/]")

        try:
            import yt_dlp

            # Progress tracking
            download_progress = {"downloaded": 0, "total": 0, "status": ""}

            def progress_hook(d):
                if d['status'] == 'downloading':
                    download_progress['downloaded'] = d.get('downloaded_bytes', 0)
                    download_progress['total'] = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    download_progress['status'] = 'downloading'
                elif d['status'] == 'finished':
                    download_progress['status'] = 'finished'

            ydl_opts = {
                'format': 'best',
                'outtmpl': str(output_path),
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [progress_hook],
            }

            # Start download in background with progress display
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task(f"[{self.theme['accent']}]Downloading...", total=100)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Start download
                    import threading
                    download_thread = threading.Thread(target=lambda: ydl.download([url]))
                    download_thread.start()

                    # Update progress bar
                    while download_thread.is_alive():
                        if download_progress['total'] > 0:
                            percent = (download_progress['downloaded'] / download_progress['total']) * 100
                            progress.update(task, completed=percent)
                        import time
                        time.sleep(0.1)

                    download_thread.join()
                    progress.update(task, completed=100)

            console.print(f"\n[{self.theme['success']}]✓ Download complete![/]")
            console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
            readchar.readkey()
            return True

        except Exception as e:
            console.print(f"\n[{self.theme['error']}]✗ Download error: {e}[/]")
            console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
            readchar.readkey()
            return False

    def convert_video(self, file: FileItem) -> bool:
        """Convert video to different format."""
        console.print()
        console.print(Panel.fit(
            f"[bold {self.theme['primary']}]🎬 Convert Video[/]\n\n"
            f"Converting: [bold]{file.path.name}[/]",
            border_style=self.theme['primary']
        ))

        # Ask for output format
        console.print(f"\n[{self.theme['accent']}]Common formats:[/]")
        console.print("  [1] MP4 (H.264)")
        console.print("  [2] MKV (copy)")
        console.print("  [3] WebM")
        console.print("  [4] AVI")
        console.print("  [5] Custom")
        console.print()
        console.print(f"[{self.theme['muted']}]Quick keys: Press 1-5 to select[/]")

        choice = Prompt.ask(f"[{self.theme['accent']}]Select format[/]", default="1")

        format_map = {
            "1": (".mp4", "libx264"),
            "2": (".mkv", "copy"),
            "3": (".webm", "libvpx"),
            "4": (".avi", "libx264"),
        }

        if choice in format_map:
            ext, codec = format_map[choice]
        elif choice == "5":
            ext = Prompt.ask(f"[{self.theme['accent']}]Enter extension (e.g., .mp4)[/]")
            if not ext.startswith('.'):
                ext = f".{ext}"
            codec = Prompt.ask(f"[{self.theme['accent']}]Enter codec (or 'copy')[/]", default="copy")
        else:
            console.print(f"[{self.theme['error']}]Invalid choice[/]")
            return False

        output_path = file.path.parent / f"{file.path.stem}_converted{ext}"

        console.print(f"\n[{self.theme['muted']}]Input:  {file.path}[/]")
        console.print(f"[{self.theme['muted']}]Output: {output_path}[/]")
        console.print(f"[{self.theme['muted']}]Codec:  {codec}[/]\n")

        if not Confirm.ask(f"[{self.theme['primary']}]Start conversion?[/]", default=True):
            return False

        try:
            stream = ffmpeg.input(str(file.path))

            if codec == 'copy':
                stream = ffmpeg.output(stream, str(output_path), codec='copy')
            else:
                stream = ffmpeg.output(stream, str(output_path), vcodec=codec)

            # Show progress spinner
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"[{self.theme['accent']}]Converting...", total=None)
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                progress.update(task, completed=100)

            output_size = output_path.stat().st_size / (1024*1024)
            console.print(f"\n[{self.theme['success']}]✓ Conversion complete![/]")
            console.print(f"  Output: {output_path.name}")
            console.print(f"  Size:   {output_size:.1f} MB")
            console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
            readchar.readkey()
            return True

        except ffmpeg.Error as e:
            console.print(f"\n[{self.theme['error']}]✗ FFmpeg error: {e}[/]")
            console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
            readchar.readkey()
            return False

    def compress_video(self, file: FileItem) -> bool:
        """Compress video with quality settings."""
        console.print()
        console.print(Panel.fit(
            f"[bold {self.theme['warning']}]🗜️  Compress Video[/]\n\n"
            f"Compressing: [bold]{file.path.name}[/]",
            border_style=self.theme['warning']
        ))

        # Ask for quality settings
        console.print(f"\n[{self.theme['accent']}]Quality presets:[/]")
        console.print(f"  [{self.theme['primary']}]1[/] High quality (CRF 18) - Large file")
        console.print(f"  [{self.theme['success']}]2[/] Good quality (CRF 23) - [bold]Recommended[/]")
        console.print(f"  [{self.theme['warning']}]3[/] Medium quality (CRF 28) - Smaller file")
        console.print(f"  [{self.theme['muted']}]4[/] Custom CRF value")
        console.print()
        console.print(f"[{self.theme['muted']}]Quick keys: Press 1-4, or h/g/m for preset[/]")
        console.print(f"[{self.theme['muted']}]  h=High  g=Good  m=Medium[/]")

        choice = Prompt.ask(f"[{self.theme['accent']}]Select quality[/]", default="2")

        # Map letter shortcuts
        shortcut_map = {"h": "1", "g": "2", "m": "3"}
        choice = shortcut_map.get(choice.lower(), choice)

        crf_map = {"1": 18, "2": 23, "3": 28}

        if choice in crf_map:
            crf = crf_map[choice]
        elif choice == "4":
            crf = int(Prompt.ask(f"[{self.theme['accent']}]Enter CRF (18-28)[/]", default="23"))
        else:
            console.print(f"[{self.theme['error']}]Invalid choice[/]")
            return False

        preset = Prompt.ask(
            f"[{self.theme['accent']}]Preset (ultrafast/fast/medium/slow/veryslow)[/]",
            default="medium"
        )

        output_path = file.path.parent / f"{file.path.stem}_compressed{file.path.suffix}"

        input_size = file.path.stat().st_size / (1024*1024)

        console.print(f"\n[{self.theme['muted']}]Input:  {file.path.name} ({input_size:.1f} MB)[/]")
        console.print(f"[{self.theme['muted']}]Output: {output_path.name}[/]")
        console.print(f"[{self.theme['muted']}]CRF:    {crf} (lower=better quality)[/]")
        console.print(f"[{self.theme['muted']}]Preset: {preset}[/]\n")

        if not Confirm.ask(f"[{self.theme['warning']}]Start compression?[/]", default=True):
            return False

        try:
            stream = ffmpeg.input(str(file.path))
            stream = ffmpeg.output(
                stream,
                str(output_path),
                vcodec='libx264',
                crf=crf,
                preset=preset,
                acodec='aac'
            )

            # Show progress spinner
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"[{self.theme['accent']}]Compressing (this may take a while)...", total=None)
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                progress.update(task, completed=100)

            output_size = output_path.stat().st_size / (1024*1024)
            reduction = ((input_size - output_size) / input_size) * 100

            console.print(f"\n[{self.theme['success']}]✓ Compression complete![/]")
            console.print(f"  Input:  {input_size:.1f} MB")
            console.print(f"  Output: {output_size:.1f} MB")
            console.print(f"  Saved:  {reduction:.1f}%")
            console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
            readchar.readkey()
            return True

        except ffmpeg.Error as e:
            console.print(f"\n[{self.theme['error']}]✗ FFmpeg error: {e}[/]")
            console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
            readchar.readkey()
            return False

    def quick_compress(self, file: FileItem, crf: int, preset: str) -> bool:
        """Quick compress without prompts - for keyboard shortcuts."""
        output_path = file.path.parent / f"{file.path.stem}_compressed{file.path.suffix}"
        input_size = file.path.stat().st_size / (1024*1024)

        try:
            stream = ffmpeg.input(str(file.path))
            stream = ffmpeg.output(
                stream,
                str(output_path),
                vcodec='libx264',
                crf=crf,
                preset=preset,
                acodec='aac'
            )

            # Show minimal progress
            console.print(f"\n[{self.theme['accent']}]⚡ Quick compress: CRF {crf}[/]")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"[{self.theme['accent']}]Compressing...", total=None)
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                progress.update(task, completed=100)

            output_size = output_path.stat().st_size / (1024*1024)
            reduction = ((input_size - output_size) / input_size) * 100

            console.print(f"[{self.theme['success']}]✓ Saved {reduction:.0f}% ({input_size:.1f}→{output_size:.1f}MB)[/]")
            import time
            time.sleep(1.5)  # Brief pause to show result
            return True

        except ffmpeg.Error as e:
            console.print(f"[{self.theme['error']}]✗ Error: {e}[/]")
            import time
            time.sleep(2)
            return False

    def extract_audio(self, file: FileItem) -> bool:
        """Extract audio from video."""
        console.print()
        console.print(Panel.fit(
            f"[bold {self.theme['success']}]🎵 Extract Audio[/]\n\n"
            f"From: [bold]{file.path.name}[/]",
            border_style=self.theme['success']
        ))

        # Ask for format
        console.print(f"\n[{self.theme['accent']}]Audio formats:[/]")
        console.print(f"  [{self.theme['success']}]1[/] MP3 (320k) - [bold]Recommended[/]")
        console.print(f"  [{self.theme['primary']}]2[/] M4A (AAC 256k)")
        console.print(f"  [{self.theme['accent']}]3[/] FLAC (lossless)")
        console.print(f"  [{self.theme['muted']}]4[/] WAV (uncompressed)")
        console.print()
        console.print(f"[{self.theme['muted']}]Quick keys: Press 1-4, or m/a/f/w for format[/]")
        console.print(f"[{self.theme['muted']}]  m=MP3  a=M4A  f=FLAC  w=WAV[/]")

        choice = Prompt.ask(f"[{self.theme['accent']}]Select format[/]", default="1")

        # Map letter shortcuts
        shortcut_map = {"m": "1", "a": "2", "f": "3", "w": "4"}
        choice = shortcut_map.get(choice.lower(), choice)

        format_map = {
            "1": ("mp3", "libmp3lame", "320k"),
            "2": ("m4a", "aac", "256k"),
            "3": ("flac", "flac", None),
            "4": ("wav", "pcm_s16le", None),
        }

        if choice not in format_map:
            console.print(f"[{self.theme['error']}]Invalid choice[/]")
            return False

        ext, codec, bitrate = format_map[choice]
        output_path = file.path.parent / f"{file.path.stem}.{ext}"

        console.print(f"\n[{self.theme['muted']}]Input:  {file.path.name}[/]")
        console.print(f"[{self.theme['muted']}]Output: {output_path.name}[/]")
        console.print(f"[{self.theme['muted']}]Format: {ext.upper()}[/]\n")

        if not Confirm.ask(f"[{self.theme['success']}]Extract audio?[/]", default=True):
            return False

        try:
            stream = ffmpeg.input(str(file.path))

            output_opts = {'acodec': codec, 'vn': None}
            if bitrate:
                output_opts['audio_bitrate'] = bitrate

            stream = ffmpeg.output(stream, str(output_path), **output_opts)

            # Show progress spinner
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"[{self.theme['accent']}]Extracting audio...", total=None)
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                progress.update(task, completed=100)

            output_size = output_path.stat().st_size / (1024*1024)
            console.print(f"\n[{self.theme['success']}]✓ Audio extraction complete![/]")
            console.print(f"  Output: {output_path.name}")
            console.print(f"  Size:   {output_size:.1f} MB")
            console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
            readchar.readkey()
            return True

        except ffmpeg.Error as e:
            console.print(f"\n[{self.theme['error']}]✗ FFmpeg error: {e}[/]")
            console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
            readchar.readkey()
            return False

    def trim_video(self, file: FileItem) -> bool:
        """Trim/cut video."""
        console.print()
        console.print(Panel.fit(
            f"[bold {self.theme['primary']}]✂️  Trim Video[/]\n\n"
            f"Trimming: [bold]{file.path.name}[/]",
            border_style=self.theme['primary']
        ))

        # Get time inputs
        start = Prompt.ask(f"[{self.theme['accent']}]Start time (HH:MM:SS)[/]", default="00:00:00")

        console.print(f"\n[{self.theme['muted']}]Specify end time OR duration (not both)[/]")
        end = Prompt.ask(f"[{self.theme['accent']}]End time (HH:MM:SS) - or leave blank[/]", default="")
        duration = ""

        if not end:
            duration = Prompt.ask(f"[{self.theme['accent']}]Duration (HH:MM:SS)[/]", default="")

        if not end and not duration:
            console.print(f"[{self.theme['error']}]✗ Must specify either end time or duration[/]")
            return False

        output_path = file.path.parent / f"{file.path.stem}_trimmed{file.path.suffix}"

        console.print(f"\n[{self.theme['muted']}]Input:  {file.path.name}[/]")
        console.print(f"[{self.theme['muted']}]Output: {output_path.name}[/]")
        console.print(f"[{self.theme['muted']}]Start:  {start}[/]")
        if end:
            console.print(f"[{self.theme['muted']}]End:    {end}[/]")
        if duration:
            console.print(f"[{self.theme['muted']}]Duration: {duration}[/]\n")

        if not Confirm.ask(f"[{self.theme['primary']}]Start trim?[/]", default=True):
            return False

        try:
            stream = ffmpeg.input(str(file.path), ss=start)

            if end:
                stream = ffmpeg.output(stream, str(output_path), to=end, codec='copy')
            else:
                stream = ffmpeg.output(stream, str(output_path), t=duration, codec='copy')

            # Show progress spinner
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"[{self.theme['accent']}]Trimming...", total=None)
                ffmpeg.run(stream, overwrite_output=True, quiet=True)
                progress.update(task, completed=100)

            output_size = output_path.stat().st_size / (1024*1024)
            console.print(f"\n[{self.theme['success']}]✓ Trim complete![/]")
            console.print(f"  Output: {output_path.name}")
            console.print(f"  Size:   {output_size:.1f} MB")
            console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
            readchar.readkey()
            return True

        except ffmpeg.Error as e:
            console.print(f"\n[{self.theme['error']}]✗ FFmpeg error: {e}[/]")
            console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
            readchar.readkey()
            return False

    def toggle_mark_file(self, files: List[FileItem]) -> str:
        """Toggle marking of current file for batch processing."""
        offset = 1 if self.current_path != self.current_path.parent else 0
        actual_idx = self.selected_index - offset

        if 0 <= actual_idx < len(files):
            file = files[actual_idx]
            if not file.is_dir:
                if file.path in self.marked_files:
                    self.marked_files.remove(file.path)
                    return f"Unmarked: {file.path.name}"
                else:
                    self.marked_files.add(file.path)
                    return f"Marked: {file.path.name}"
        return "Cannot mark directories"

    def mark_all_files(self, files: List[FileItem]) -> str:
        """Mark all non-directory files in current view."""
        count = 0
        for file in files:
            if not file.is_dir:
                self.marked_files.add(file.path)
                count += 1
        return f"Marked {count} files"

    def unmark_all_files(self) -> str:
        """Clear all marked files."""
        count = len(self.marked_files)
        self.marked_files.clear()
        return f"Unmarked {count} files"

    def batch_compress(self, crf: int = 23, preset: str = "medium") -> bool:
        """Compress all marked files with progress display."""
        if not self.marked_files:
            console.print(f"[{self.theme['warning']}]No files marked for batch processing[/]")
            import time
            time.sleep(1.5)
            return False

        files_to_process = list(self.marked_files)
        total_files = len(files_to_process)

        console.print()
        console.print(Panel.fit(
            f"[bold {self.theme['warning']}]🗜️  Batch Compress[/]\n\n"
            f"Processing {total_files} files\n"
            f"Quality: CRF {crf}, Preset: {preset}",
            border_style=self.theme['warning']
        ))
        console.print()

        if not Confirm.ask(f"[{self.theme['warning']}]Start batch compression?[/]", default=True):
            return False

        results = {"success": 0, "failed": 0, "skipped": 0}
        total_saved = 0.0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[{self.theme['accent']}]Compressing files...", total=total_files)

            for idx, file_path in enumerate(files_to_process, 1):
                if not file_path.exists():
                    results["skipped"] += 1
                    progress.update(task, advance=1, description=f"[{self.theme['warning']}]Skipped: {file_path.name}")
                    continue

                progress.update(task, description=f"[{self.theme['accent']}]Compressing {idx}/{total_files}: {file_path.name}")

                output_path = file_path.parent / f"{file_path.stem}_compressed{file_path.suffix}"
                input_size = file_path.stat().st_size / (1024*1024)

                try:
                    stream = ffmpeg.input(str(file_path))
                    stream = ffmpeg.output(
                        stream,
                        str(output_path),
                        vcodec='libx264',
                        crf=crf,
                        preset=preset,
                        acodec='aac'
                    )
                    ffmpeg.run(stream, overwrite_output=True, quiet=True, capture_stderr=True)

                    output_size = output_path.stat().st_size / (1024*1024)
                    saved = input_size - output_size
                    total_saved += saved

                    results["success"] += 1
                except Exception as e:
                    results["failed"] += 1
                    progress.update(task, description=f"[{self.theme['error']}]Failed: {file_path.name}")

                progress.update(task, advance=1)

        # Show summary
        console.print()
        console.print(f"[bold {self.theme['success']}]✓ Batch compression complete![/]")
        console.print(f"  Successful: {results['success']}")
        console.print(f"  Failed:     {results['failed']}")
        console.print(f"  Skipped:    {results['skipped']}")
        console.print(f"  Total saved: {total_saved:.1f} MB")
        console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
        readchar.readkey()

        # Clear marked files after processing
        self.marked_files.clear()
        return True

    def batch_url_download(self) -> bool:
        """Download all URLs in the batch queue."""
        if not self.batch_url_queue:
            console.print(f"[{self.theme['warning']}]No URLs in download queue[/]")
            import time
            time.sleep(1.5)
            return False

        total_urls = len(self.batch_url_queue)

        console.print()
        console.print(Panel.fit(
            f"[bold {self.theme['primary']}]📥 Batch Download[/]\n\n"
            f"Processing {total_urls} URLs",
            border_style=self.theme['primary']
        ))
        console.print()

        if not Confirm.ask(f"[{self.theme['primary']}]Start batch download?[/]", default=True):
            return False

        results = {"success": 0, "failed": 0}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task(f"[{self.theme['accent']}]Downloading...", total=total_urls)

            for idx, url in enumerate(self.batch_url_queue, 1):
                progress.update(task, description=f"[{self.theme['accent']}]Downloading {idx}/{total_urls}")

                try:
                    import yt_dlp

                    output_path = self.current_path / "%(title)s.%(ext)s"
                    ydl_opts = {
                        'format': 'best',
                        'outtmpl': str(output_path),
                        'quiet': True,
                        'no_warnings': True,
                    }

                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])

                    results["success"] += 1
                except Exception as e:
                    results["failed"] += 1
                    progress.update(task, description=f"[{self.theme['error']}]Failed: {url[:50]}...")

                progress.update(task, advance=1)

        # Show summary
        console.print()
        console.print(f"[bold {self.theme['success']}]✓ Batch download complete![/]")
        console.print(f"  Successful: {results['success']}")
        console.print(f"  Failed:     {results['failed']}")
        console.print(f"\n[{self.theme['muted']}]Press any key to continue...[/]")
        readchar.readkey()

        # Clear queue after processing
        self.batch_url_queue.clear()
        return True

    def manage_url_queue(self) -> bool:
        """Manage the batch URL download queue."""
        while True:
            console.clear()
            console.print(Panel.fit(
                f"[bold {self.theme['primary']}]📋 Batch URL Queue Manager[/]",
                border_style=self.theme['primary']
            ))
            console.print()

            if self.batch_url_queue:
                console.print(f"[{self.theme['accent']}]URLs in queue ({len(self.batch_url_queue)}):[/]")
                for idx, url in enumerate(self.batch_url_queue, 1):
                    console.print(f"  {idx}. {url}")
                console.print()
            else:
                console.print(f"[{self.theme['muted']}]Queue is empty[/]")
                console.print()

            console.print(f"[{self.theme['accent']}]Options:[/]")
            console.print("  [a] Add URL to queue")
            console.print("  [r] Remove URL from queue")
            console.print("  [c] Clear entire queue")
            console.print("  [d] Download all URLs now")
            console.print("  [q] Back to file browser")
            console.print()

            key = readchar.readkey()

            if key.lower() == 'a':
                url = Prompt.ask(f"[{self.theme['accent']}]Enter URL[/]")
                if url:
                    self.batch_url_queue.append(url)
                    console.print(f"[{self.theme['success']}]✓ Added to queue[/]")
                    import time
                    time.sleep(1)

            elif key.lower() == 'r' and self.batch_url_queue:
                idx_str = Prompt.ask(f"[{self.theme['accent']}]Enter number to remove[/]")
                try:
                    idx = int(idx_str) - 1
                    if 0 <= idx < len(self.batch_url_queue):
                        removed = self.batch_url_queue.pop(idx)
                        console.print(f"[{self.theme['success']}]✓ Removed: {removed}[/]")
                    import time
                    time.sleep(1)
                except ValueError:
                    pass

            elif key.lower() == 'c':
                if Confirm.ask(f"[{self.theme['error']}]Clear entire queue?[/]", default=False):
                    count = len(self.batch_url_queue)
                    self.batch_url_queue.clear()
                    console.print(f"[{self.theme['success']}]✓ Cleared {count} URLs[/]")
                    import time
                    time.sleep(1)

            elif key.lower() == 'd':
                self.batch_url_download()
                break

            elif key.lower() == 'q':
                break

        return True

    def show_options_menu(self):
        """Display options and about information."""
        console.clear()

        # Header
        console.print(Panel.fit(
            f"[bold {self.theme['primary']}]⚙️  fftpeg Options[/]",
            style=self.theme['primary'],
            border_style=self.theme['border']
        ))
        console.print()

        # About section
        about_text = f"""[bold {self.theme['accent']}]fftpeg - Terminal FFmpeg[/]
[{self.theme['muted']}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]

[b]Version:[/] 0.1.0
[b]License:[/] Apache 2.0

[{self.theme['muted']}]A modern TUI and CLI for ffmpeg operations[/]

[b {self.theme['accent']}]Features:[/]
• Download videos with yt-dlp
• Convert video formats
• Compress videos
• Extract audio
• Trim/cut videos
• Smart file organization
• Configurable filters
• Theme auto-detection

[{self.theme['muted']}]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/]

[b {self.theme['accent']}]Current Configuration:[/]"""

        console.print(about_text)
        console.print()

        # Configuration table
        config_table = Table.grid(padding=(0, 2))
        config_table.add_column(style=self.theme['accent'])
        config_table.add_column(style="white")

        config_table.add_row(f"[{self.theme['accent']}]Theme:[/]", self.theme_name)
        config_table.add_row(f"[{self.theme['accent']}]Theme Source:[/]", "vim/neovim auto-detect")
        config_table.add_row(f"[{self.theme['accent']}]Filter:[/]", FILTER_TYPES[self.current_filter]['label'])
        config_table.add_row(f"[{self.theme['accent']}]Show Hidden:[/]", "Yes" if self.show_hidden else "No")
        config_table.add_row(f"[{self.theme['accent']}]Working Dir:[/]", str(self.current_path))

        console.print(config_table)
        console.print()

        # Keybindings table
        console.print(f"[bold {self.theme['accent']}]Keybindings:[/]")
        console.print()

        kb_table = Table(box=box.SIMPLE, border_style=self.theme['border'])
        kb_table.add_column("Key", style=self.theme['primary'], no_wrap=True)
        kb_table.add_column("Action", style="white")
        kb_table.add_column("Description", style=self.theme['muted'])

        keybindings = [
            ("↑/k", "Up", "Navigate up one item"),
            ("↓/j", "Down", "Navigate down one item"),
            ("PgUp", "Page Up", "Jump up one page"),
            ("PgDn", "Page Down", "Jump down one page"),
            ("g", "Home", "Jump to first item"),
            ("G", "End", "Jump to last item"),
            ("Enter", "Select", "Enter directory or select file"),
            ("U", "Pull", "Download video from URL"),
            ("I", "Import", "Import file from path"),
            ("M", "Move", "Move file to new location"),
            ("Del", "Delete", "Delete selected file"),
            ("C", "Convert", "Convert video format (interactive)"),
            ("P", "Compress", "Compress video (interactive)"),
            ("!", "Quick High", "Compress CRF 18 (instant, no prompts)"),
            ("@", "Quick Good", "Compress CRF 23 (instant, no prompts)"),
            ("#", "Quick Med", "Compress CRF 28 (instant, no prompts)"),
            ("A", "Audio", "Extract audio from video"),
            ("T", "Trim", "Trim/cut video"),
            ("R", "Refresh", "Refresh file list"),
            ("N", "Rename", "Rename selected file"),
            ("F", "Filter", "Cycle file type filters"),
            ("H", "Hidden", "Toggle hidden files"),
            ("Ctrl+F", "Toggle Filter", "Toggle filter on/off"),
            ("O", "Options", "Show this menu"),
            ("Q", "Quit", "Exit application"),
        ]

        for key, action, desc in keybindings:
            kb_table.add_row(key, action, desc)

        console.print(kb_table)
        console.print()

        # Theme colors preview
        console.print(f"[bold {self.theme['accent']}]Theme Colors:[/]")
        console.print(
            f"[{self.theme['primary']}]█[/] Primary  "
            f"[{self.theme['secondary']}]█[/] Secondary  "
            f"[{self.theme['accent']}]█[/] Accent  "
            f"[{self.theme['success']}]█[/] Success  "
            f"[{self.theme['warning']}]█[/] Warning  "
            f"[{self.theme['error']}]█[/] Error"
        )
        console.print()

        console.print(f"[{self.theme['muted']}]Press any key to return to file browser...[/]")
        readchar.readkey()

    def run(self):
        """Main application loop."""
        status_msg = ""

        while True:
            files = self.get_file_list()
            self.display_file_browser(files, status_msg)
            status_msg = ""  # Clear status after displaying

            # Get keyboard input
            try:
                key = readchar.readkey()
            except KeyboardInterrupt:
                break

            # Navigation
            if key == readchar.key.UP or key.lower() == 'k':
                self.navigate_up(files)

            elif key == readchar.key.DOWN or key.lower() == 'j':
                self.navigate_down(files)

            elif key == readchar.key.PAGE_UP:
                self.page_up(files)

            elif key == readchar.key.PAGE_DOWN:
                self.page_down(files)

            elif key == readchar.key.HOME or key.lower() == 'g':
                self.home()

            elif key == readchar.key.END or key.lower() == 'G':
                self.end(files)

            elif key == readchar.key.ENTER or key == '\r' or key == '\n':
                if not self.select_item(files):
                    break

            # Filter controls
            elif key.lower() == 'f':
                self.cycle_filter()
                status_msg = f"Filter: {FILTER_TYPES[self.current_filter]['label']}"

            elif key == '\x06':  # Ctrl+F
                self.toggle_filter()
                status_msg = "Filter: On" if self.filter_enabled else "Filter: Off"

            elif key.lower() == 'h':
                self.toggle_hidden()
                status_msg = "Hidden files: On" if self.show_hidden else "Hidden files: Off"

            elif key.lower() == 'r':
                status_msg = "Refreshed"

            # File operations
            elif key.lower() == 'u':
                if self.pull_video():
                    status_msg = "Video downloaded"
                else:
                    status_msg = "Download cancelled"

            elif key.lower() == 'i':
                if self.import_file():
                    status_msg = "File imported"
                else:
                    status_msg = "Import cancelled"

            elif key.lower() == 'm':
                selected = self.get_selected_file(files)
                if selected:
                    if self.move_file(selected):
                        status_msg = "File moved"
                    else:
                        status_msg = "Move cancelled"
                else:
                    status_msg = "Select a file to move"

            elif key == readchar.key.DELETE or key == readchar.key.BACKSPACE:
                selected = self.get_selected_file(files)
                if selected:
                    if self.delete_file(selected):
                        status_msg = "File deleted"
                    else:
                        status_msg = "Delete cancelled"
                else:
                    status_msg = "Select a file to delete"

            elif key.lower() == 'c':
                selected = self.get_selected_file(files)
                if selected:
                    if self.convert_video(selected):
                        status_msg = "Video converted"
                    else:
                        status_msg = "Conversion cancelled"
                else:
                    status_msg = "Select a video file to convert"

            elif key.lower() == 'p':
                selected = self.get_selected_file(files)
                if selected:
                    if self.compress_video(selected):
                        status_msg = "Video compressed"
                    else:
                        status_msg = "Compression cancelled"
                else:
                    status_msg = "Select a video file to compress"

            # Quick compression presets (Shift+P + quality key)
            elif key == '!':  # Shift+1 - Quick high quality compress
                selected = self.get_selected_file(files)
                if selected:
                    if self.quick_compress(selected, crf=18, preset="medium"):
                        status_msg = "Video compressed (High quality)"
                    else:
                        status_msg = "Compression failed"
                else:
                    status_msg = "Select a video file to compress"

            elif key == '@':  # Shift+2 - Quick good quality compress
                selected = self.get_selected_file(files)
                if selected:
                    if self.quick_compress(selected, crf=23, preset="medium"):
                        status_msg = "Video compressed (Good quality)"
                    else:
                        status_msg = "Compression failed"
                else:
                    status_msg = "Select a video file to compress"

            elif key == '#':  # Shift+3 - Quick medium quality compress
                selected = self.get_selected_file(files)
                if selected:
                    if self.quick_compress(selected, crf=28, preset="medium"):
                        status_msg = "Video compressed (Medium quality)"
                    else:
                        status_msg = "Compression failed"
                else:
                    status_msg = "Select a video file to compress"

            elif key.lower() == 'a':
                selected = self.get_selected_file(files)
                if selected:
                    if self.extract_audio(selected):
                        status_msg = "Audio extracted"
                    else:
                        status_msg = "Extraction cancelled"
                else:
                    status_msg = "Select a video file to extract audio"

            elif key.lower() == 't':
                selected = self.get_selected_file(files)
                if selected:
                    if self.trim_video(selected):
                        status_msg = "Video trimmed"
                    else:
                        status_msg = "Trim cancelled"
                else:
                    status_msg = "Select a video file to trim"

            elif key.lower() == 'n':
                selected = self.get_selected_file(files)
                if selected:
                    if self.rename_file(selected):
                        status_msg = "File renamed"
                    else:
                        status_msg = "Rename cancelled"
                else:
                    status_msg = "Select a file to rename"

            # Batch operations
            elif key == ' ':  # Space - toggle mark file
                status_msg = self.toggle_mark_file(files)

            elif key == 'V':  # Shift+V - mark all files
                status_msg = self.mark_all_files(files)

            elif key == '\x15':  # Ctrl+U - unmark all
                status_msg = self.unmark_all_files()

            elif key == 'B':  # Shift+B - batch compress marked files
                if self.marked_files:
                    if self.batch_compress(crf=23, preset="medium"):
                        status_msg = f"Batch compression complete"
                    else:
                        status_msg = "Batch operation cancelled"
                else:
                    status_msg = "No files marked - use Space to mark files"

            elif key == 'Q':  # Shift+Q - manage URL queue
                self.manage_url_queue()
                status_msg = ""

            elif key.lower() == 'o':
                self.show_options_menu()
                status_msg = ""

            elif key.lower() == 'q':
                console.clear()
                console.print(f"\n[{self.theme['accent']}]Goodbye![/]")
                break

        return 0
