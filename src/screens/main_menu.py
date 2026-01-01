"""Main menu screen with file browser."""

import os
import shutil
from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import Header, Footer, Static, DirectoryTree, Button, Label, Input
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileChangeHandler(FileSystemEventHandler):
    """Handler for file system events."""

    def __init__(self, callback):
        """Initialize with callback function.

        Args:
            callback: Function to call when files change
        """
        super().__init__()
        self.callback = callback

    def on_any_event(self, event):
        """Called when any file system event occurs."""
        # Ignore directory events and temporary files
        if event.is_directory or event.src_path.endswith(('.tmp', '.swp', '~')):
            return

        # Call the callback for file changes
        self.callback()


class ConfirmDeleteScreen(ModalScreen):
    """Confirmation dialog for file deletion."""

    CSS = """
    ConfirmDeleteScreen {
        align: center middle;
    }

    #delete-dialog {
        width: 60;
        height: auto;
        border: thick $error;
        background: $surface;
        padding: 1 2;
    }

    #delete-message {
        color: $text;
        text-align: center;
        padding: 1 0;
    }

    #delete-filename {
        color: $warning;
        text-style: bold;
        text-align: center;
        padding: 1 0;
    }

    #delete-buttons {
        align: center middle;
        height: auto;
        padding: 1 0;
    }

    .delete-button {
        margin: 0 1;
    }
    """

    def __init__(self, file_path: Path):
        """Initialize delete confirmation dialog.

        Args:
            file_path: Path to file to delete
        """
        super().__init__()
        self.file_path = file_path

    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog."""
        with Container(id="delete-dialog"):
            yield Label("⚠️  Delete File?", id="delete-message")
            yield Label(self.file_path.name, id="delete-filename")
            yield Label("This action cannot be undone!", id="delete-message")
            with Horizontal(id="delete-buttons"):
                yield Button("Cancel", variant="primary", classes="delete-button", id="cancel-btn")
                yield Button("Delete", variant="error", classes="delete-button", id="delete-btn")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "delete-btn":
            self.dismiss(True)
        else:
            self.dismiss(False)


class ImportFileScreen(ModalScreen):
    """Dialog for importing a file."""

    CSS = """
    ImportFileScreen {
        align: center middle;
    }

    #import-dialog {
        width: 70;
        height: auto;
        border: thick $success;
        background: $surface;
        padding: 1 2;
    }

    #import-title {
        color: $accent;
        text-style: bold;
        text-align: center;
        padding: 1 0;
        background: $primary-darken-2;
    }

    #import-label {
        color: $text-muted;
        padding: 1 0;
    }

    #import-path-input {
        margin: 0 0 1 0;
    }

    #import-buttons {
        align: center middle;
        height: auto;
        padding: 1 0;
    }

    .import-button {
        margin: 0 1;
    }

    #import-hint {
        color: $text-muted;
        text-style: italic;
        text-align: center;
        padding: 1 0;
    }
    """

    def __init__(self, target_dir: Path):
        """Initialize import dialog.

        Args:
            target_dir: Directory to import file into
        """
        super().__init__()
        self.target_dir = target_dir

    def compose(self) -> ComposeResult:
        """Compose the import dialog."""
        with Container(id="import-dialog"):
            yield Label("📥 Import File", id="import-title")
            yield Label("Enter file path to import:", id="import-label")
            yield Input(
                placeholder="e.g., /home/user/downloads/video.mp4",
                id="import-path-input"
            )
            yield Label("File will be copied to current directory", id="import-hint")
            with Horizontal(id="import-buttons"):
                yield Button("Cancel", variant="default", classes="import-button", id="cancel-btn")
                yield Button("Import", variant="success", classes="import-button", id="import-btn")

    def on_mount(self) -> None:
        """Focus input when mounted."""
        self.query_one("#import-path-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "import-btn":
            input_widget = self.query_one("#import-path-input", Input)
            file_path = input_widget.value.strip()
            if file_path:
                self.dismiss(Path(file_path))
            else:
                self.dismiss(None)
        else:
            self.dismiss(None)


class MoveFileScreen(ModalScreen):
    """Dialog for moving a file."""

    CSS = """
    MoveFileScreen {
        align: center middle;
    }

    #move-dialog {
        width: 70;
        height: auto;
        border: thick $warning;
        background: $surface;
        padding: 1 2;
    }

    #move-title {
        color: $accent;
        text-style: bold;
        text-align: center;
        padding: 1 0;
        background: $primary-darken-2;
    }

    #move-label {
        color: $text-muted;
        padding: 1 0;
    }

    #move-current-file {
        color: $warning;
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
    }

    #move-path-input {
        margin: 0 0 1 0;
    }

    #move-buttons {
        align: center middle;
        height: auto;
        padding: 1 0;
    }

    .move-button {
        margin: 0 1;
    }

    #move-hint {
        color: $text-muted;
        text-style: italic;
        text-align: center;
        padding: 1 0;
    }
    """

    def __init__(self, source_file: Path):
        """Initialize move dialog.

        Args:
            source_file: File to be moved
        """
        super().__init__()
        self.source_file = source_file

    def compose(self) -> ComposeResult:
        """Compose the move dialog."""
        with Container(id="move-dialog"):
            yield Label("📦 Move File", id="move-title")
            yield Label(f"Moving: {self.source_file.name}", id="move-current-file")
            yield Label("Enter destination path:", id="move-label")
            yield Input(
                placeholder="e.g., /home/user/videos/",
                value=str(self.source_file.parent) + "/",
                id="move-path-input"
            )
            yield Label("File will be moved to new location", id="move-hint")
            with Horizontal(id="move-buttons"):
                yield Button("Cancel", variant="default", classes="move-button", id="cancel-btn")
                yield Button("Move", variant="warning", classes="move-button", id="move-btn")

    def on_mount(self) -> None:
        """Focus input when mounted."""
        self.query_one("#move-path-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "move-btn":
            input_widget = self.query_one("#move-path-input", Input)
            dest_path = input_widget.value.strip()
            if dest_path:
                self.dismiss(Path(dest_path))
            else:
                self.dismiss(None)
        else:
            self.dismiss(None)


class MediaDirectoryTree(DirectoryTree):
    """A directory tree that can filter for media files."""

    VIDEO_EXTENSIONS = {
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
        ".m4v", ".mpg", ".mpeg", ".3gp", ".ogv", ".ts", ".m2ts"
    }

    IMAGE_EXTENSIONS = {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg",
        ".tiff", ".tif", ".ico", ".heic", ".heif", ".raw", ".cr2", ".nef"
    }

    AUDIO_EXTENSIONS = {
        ".mp3", ".m4a", ".wav", ".flac", ".aac", ".ogg", ".wma", ".opus"
    }

    ALL_MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS | AUDIO_EXTENSIONS

    def __init__(self, *args, filter_mode=None, show_hidden=False, **kwargs):
        """Initialize with optional filter mode.

        Args:
            filter_mode: None (show all), "video", "image", "audio", or "media" (all media types)
            show_hidden: Whether to show hidden files/folders (default: False)
        """
        super().__init__(*args, **kwargs)
        self.filter_mode = filter_mode
        self.show_hidden = show_hidden

    def _folder_contains_filetype(self, folder_path, extensions, max_depth=3, current_depth=0):
        """Check if folder contains files with given extensions (recursive).

        Args:
            folder_path: Path to folder to check
            extensions: Set of file extensions to look for
            max_depth: Maximum depth to search (prevent infinite recursion)
            current_depth: Current recursion depth

        Returns:
            True if folder or any subfolder contains matching files
        """
        if current_depth >= max_depth:
            return False

        try:
            for item in folder_path.iterdir():
                # Skip hidden files if show_hidden is False
                if not self.show_hidden and item.name.startswith('.'):
                    continue

                # Check if it's a matching file
                if item.is_file() and item.suffix.lower() in extensions:
                    return True

                # Recurse into subdirectories
                if item.is_dir():
                    if self._folder_contains_filetype(item, extensions, max_depth, current_depth + 1):
                        return True
        except (PermissionError, OSError):
            # Can't access folder, assume it doesn't contain matches
            pass

        return False

    def filter_paths(self, paths):
        """Filter paths based on current filter mode and hidden file visibility."""
        # First filter hidden files if needed
        if not self.show_hidden:
            paths = [path for path in paths if not path.name.startswith('.')]

        # Then apply media type filter
        if self.filter_mode is None:
            # No media filter active - show everything (except hidden if disabled)
            return paths

        # Filter based on mode
        if self.filter_mode == "video":
            extensions = self.VIDEO_EXTENSIONS
        elif self.filter_mode == "image":
            extensions = self.IMAGE_EXTENSIONS
        elif self.filter_mode == "audio":
            extensions = self.AUDIO_EXTENSIONS
        elif self.filter_mode == "media":
            extensions = self.ALL_MEDIA_EXTENSIONS
        else:
            # Unknown mode, show all
            return paths

        # Filter files and directories
        filtered = []
        for path in paths:
            if path.is_file():
                # Include file if it matches extension
                if path.suffix.lower() in extensions:
                    filtered.append(path)
            elif path.is_dir():
                # Include directory only if it contains matching files in subfolders
                if self._folder_contains_filetype(path, extensions):
                    filtered.append(path)

        return filtered


class MainMenuScreen(Screen):
    """The main menu screen with file browser."""

    CSS = """
    MainMenuScreen {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 3fr 2fr;
    }

    #file-browser {
        border: thick $primary;
        border-title-align: center;
        height: 100%;
        padding: 1;
        background: $surface;
    }

    #info-panel {
        border: thick $secondary;
        border-title-align: center;
        height: 100%;
        padding: 1;
        background: $surface;
    }

    DirectoryTree {
        height: 100%;
        background: $surface;
    }

    DirectoryTree > .tree--guides {
        color: $primary-lighten-2;
    }

    DirectoryTree:focus {
        border: tall $accent;
    }

    .info-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        text-align: center;
        background: $primary-darken-2;
        padding: 1;
    }

    .info-content {
        padding: 1 2;
        color: $text;
    }

    .info-label {
        color: $text-muted;
        width: 15;
    }

    .info-value {
        color: $success;
        text-style: bold;
    }

    .welcome-box {
        border: solid $accent;
        background: $boost;
        padding: 1 2;
        margin: 1 0;
    }

    .operation-hint {
        color: $warning;
        text-style: italic;
        margin-top: 1;
    }

    .file-name {
        color: $accent;
        text-style: bold;
        text-align: center;
        padding: 1;
        background: $primary-darken-3;
    }

    .stat-row {
        margin: 0 0 0 2;
    }
    """

    BINDINGS = [
        Binding("u", "pull", "Pull URL", show=True),
        Binding("c", "convert", "Convert", show=True),
        Binding("p", "compress", "Compress", show=True),
        Binding("a", "audio", "Audio", show=True),
        Binding("t", "trim", "Trim", show=False),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("n", "rename", "Rename", show=False),
        Binding("m", "move_file", "Move", show=True),
        Binding("delete", "delete_file", "Delete", show=True),
        Binding("i", "import_file", "Import", show=True),
        Binding("d", "dedupe", "Dedupe", show=False),
        Binding("f", "filter", "Filter", show=True),
        Binding("ctrl+f", "toggle_filter_enabled", "Filter On/Off", show=False),
        Binding("h", "toggle_hidden", "Hidden", show=True),
        Binding("o", "options", "Options", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, start_path: Path):
        """Initialize the main menu screen.

        Args:
            start_path: The directory to start browsing from
        """
        super().__init__()
        self.start_path = start_path
        self.selected_file = None
        self.current_filter = "media"  # Default filter type
        self.filter_enabled = True  # Filter is enabled by default
        self.show_hidden = False  # Hidden files disabled by default
        self.file_observer = None  # File system watcher

    def _get_welcome_message(self) -> str:
        """Get the welcome message for the info panel."""
        return """[b cyan]Welcome to fftpeg! 🎬[/b cyan]

[yellow]━━━━━━━━━━━━━━━━━━━━━━━[/yellow]

[dim]Navigate the file browser with[/dim]
[dim]arrow keys and select a video[/dim]
[dim]file to get started.[/dim]

[yellow]━━━━━━━━━━━━━━━━━━━━━━━[/yellow]

[dim italic]⚡ Available Operations:[/dim italic]

  [bold green]U[/bold green] → Pull from URL ⭐
  [bold green]I[/bold green] → Import file
  [bold cyan]C[/bold cyan] → Convert format
  [bold cyan]P[/bold cyan] → Compress video
  [bold cyan]A[/bold cyan] → Extract audio

[yellow]━━━━━━━━━━━━━━━━━━━━━━━[/yellow]

[dim]Press [bold]Q[/bold] to quit[/dim]
[dim]Press [bold]?[/bold] for help[/dim]
"""

    def compose(self) -> ComposeResult:
        """Compose the main menu screen."""
        yield Header()

        with Container(id="file-browser"):
            yield Static("📁 File Browser", classes="info-title")
            # Only apply filter if enabled, otherwise pass None
            filter_mode = self.current_filter if self.filter_enabled else None
            yield MediaDirectoryTree(str(self.start_path), filter_mode=filter_mode, show_hidden=self.show_hidden)

        with Container(id="info-panel"):
            yield Static("ℹ️  File Information", classes="info-title")
            yield Static(
                self._get_welcome_message(),
                id="file-info",
                classes="info-content"
            )

        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted - start file watcher."""
        self.start_file_watcher()

    def on_unmount(self) -> None:
        """Called when screen is unmounted - stop file watcher."""
        self.stop_file_watcher()

    def start_file_watcher(self) -> None:
        """Start watching the current directory for file changes."""
        try:
            self.file_observer = Observer()
            event_handler = FileChangeHandler(self.refresh_tree)
            self.file_observer.schedule(event_handler, str(self.start_path), recursive=True)
            self.file_observer.start()
        except Exception as e:
            # If watcher fails, just continue without it
            self.app.notify(f"File watcher disabled: {e}", severity="warning")

    def stop_file_watcher(self) -> None:
        """Stop the file watcher."""
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
            self.file_observer = None

    def refresh_tree(self) -> None:
        """Refresh the directory tree."""
        # Use call_from_thread since watchdog runs in a different thread
        self.app.call_from_thread(self._do_refresh)

    def _do_refresh(self) -> None:
        """Actually perform the tree refresh (runs in main thread)."""
        try:
            tree = self.query_one(MediaDirectoryTree)
            tree.reload()
        except Exception:
            # Tree might not be ready, ignore
            pass

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection in the directory tree."""
        self.selected_file = event.path
        self.update_file_info(event.path)

    def update_file_info(self, file_path: Path) -> None:
        """Update the file information panel.

        Args:
            file_path: The selected file path
        """
        info_widget = self.query_one("#file-info", Static)

        # Get basic file stats
        stat = file_path.stat()
        size_mb = stat.st_size / (1024 * 1024)

        # Format size nicely
        if size_mb < 1:
            size_str = f"{stat.st_size / 1024:.1f} KB"
        elif size_mb < 1024:
            size_str = f"{size_mb:.1f} MB"
        else:
            size_str = f"{size_mb / 1024:.2f} GB"

        info_text = f"""[b cyan]{file_path.name}[/b cyan]

[yellow]━━━━━━━━━━━━━━━━━━━━━━━[/yellow]

[dim]📦 Size:[/dim]       [green bold]{size_str}[/green bold]
[dim]🎬 Format:[/dim]     [green bold]{file_path.suffix[1:].upper()}[/green bold]
[dim]📂 Location:[/dim]   [blue]{file_path.parent.name}/[/blue]

[yellow]━━━━━━━━━━━━━━━━━━━━━━━[/yellow]

[dim italic]⚡ Quick Actions:[/dim italic]

  [bold cyan]C[/bold cyan] → Convert format
  [bold cyan]P[/bold cyan] → Compress video
  [bold cyan]A[/bold cyan] → Extract audio
  [bold cyan]T[/bold cyan] → Trim video
  [bold red]Del[/bold red] → Delete file

[yellow]━━━━━━━━━━━━━━━━━━━━━━━[/yellow]
"""

        info_widget.update(info_text)

    def action_pull(self) -> None:
        """Handle pull URL action."""
        from .pull_screen import PullScreen
        self.app.push_screen(PullScreen())

    def action_convert(self) -> None:
        """Handle convert action."""
        if self.selected_file:
            self.app.notify(f"Convert: {self.selected_file.name}", severity="information")
        else:
            self.app.notify("Please select a file first", severity="warning")

    def action_compress(self) -> None:
        """Handle compress action."""
        if self.selected_file:
            self.app.notify(f"Compress: {self.selected_file.name}", severity="information")
        else:
            self.app.notify("Please select a file first", severity="warning")

    def action_audio(self) -> None:
        """Handle audio extraction action."""
        if self.selected_file:
            self.app.notify(f"Audio: {self.selected_file.name}", severity="information")
        else:
            self.app.notify("Please select a file first", severity="warning")

    def action_trim(self) -> None:
        """Handle trim action."""
        if self.selected_file:
            self.app.notify(f"Trim: {self.selected_file.name}", severity="information")
        else:
            self.app.notify("Please select a file first", severity="warning")

    def action_refresh(self) -> None:
        """Manually refresh the directory tree."""
        self._do_refresh()
        self.app.notify("File list refreshed", severity="information")

    def action_rename(self) -> None:
        """Handle rename action."""
        if self.selected_file:
            self.app.notify(f"Rename: {self.selected_file.name} (coming soon)", severity="information")
        else:
            self.app.notify("Please select a file first", severity="warning")

    def action_dedupe(self) -> None:
        """Handle dedupe action."""
        self.app.notify("Dedupe feature coming soon!", severity="information")

    def action_filter(self) -> None:
        """Cycle through media filter types: media -> video -> image -> audio -> media."""
        filters = ["media", "video", "image", "audio"]
        try:
            current_index = filters.index(self.current_filter)
        except ValueError:
            current_index = 0

        next_index = (current_index + 1) % len(filters)
        self.current_filter = filters[next_index]

        # Update the tree with new filter (only if filter is enabled)
        tree = self.query_one(MediaDirectoryTree)
        tree.filter_mode = self.current_filter if self.filter_enabled else None
        tree.reload()

        # Notify user
        filter_names = {
            "media": "All Media (Video/Audio/Image)",
            "video": "Videos Only",
            "image": "Images Only",
            "audio": "Audio Only"
        }
        status = "ON" if self.filter_enabled else "OFF"
        self.app.notify(f"Filter: {filter_names[self.current_filter]} [{status}]", severity="information")

    def action_toggle_filter_enabled(self) -> None:
        """Toggle filter on/off completely (Ctrl+F)."""
        self.filter_enabled = not self.filter_enabled

        # Update the tree
        tree = self.query_one(MediaDirectoryTree)
        tree.filter_mode = self.current_filter if self.filter_enabled else None
        tree.reload()

        # Notify user
        if self.filter_enabled:
            filter_names = {
                "media": "All Media",
                "video": "Videos",
                "image": "Images",
                "audio": "Audio"
            }
            self.app.notify(f"Filter: ON ({filter_names[self.current_filter]})", severity="information")
        else:
            self.app.notify("Filter: OFF (showing all files)", severity="information")

    def action_toggle_hidden(self) -> None:
        """Toggle visibility of hidden files and folders."""
        self.show_hidden = not self.show_hidden

        # Update the tree
        tree = self.query_one(MediaDirectoryTree)
        tree.show_hidden = self.show_hidden
        tree.reload()

        # Notify user
        status = "shown" if self.show_hidden else "hidden"
        self.app.notify(f"Hidden files: {status}", severity="information")

    def action_options(self) -> None:
        """Open options screen."""
        from .options_screen import OptionsScreen
        self.app.push_screen(OptionsScreen())

    async def action_delete_file(self) -> None:
        """Delete the selected file with confirmation."""
        if not self.selected_file:
            self.app.notify("Please select a file first", severity="warning")
            return

        if not self.selected_file.is_file():
            self.app.notify("Can only delete files, not directories", severity="warning")
            return

        # Show confirmation dialog
        confirmed = await self.app.push_screen_wait(ConfirmDeleteScreen(self.selected_file))

        if confirmed:
            try:
                # Delete the file
                self.selected_file.unlink()
                self.app.notify(f"Deleted: {self.selected_file.name}", severity="success")

                # Clear selection and refresh
                self.selected_file = None
                self._do_refresh()

                # Reset info panel to welcome message
                info_widget = self.query_one("#file-info", Static)
                info_widget.update(self._get_welcome_message())
            except Exception as e:
                self.app.notify(f"Error deleting file: {e}", severity="error")

    async def action_import_file(self) -> None:
        """Import a file from another location."""
        # Determine target directory (current directory or selected directory)
        if self.selected_file and self.selected_file.is_dir():
            target_dir = self.selected_file
        else:
            target_dir = self.start_path

        # Show import dialog
        source_path = await self.app.push_screen_wait(ImportFileScreen(target_dir))

        if source_path:
            try:
                # Validate source file exists
                if not source_path.exists():
                    self.app.notify(f"File not found: {source_path}", severity="error")
                    return

                if not source_path.is_file():
                    self.app.notify("Can only import files, not directories", severity="warning")
                    return

                # Determine destination
                dest_path = target_dir / source_path.name

                # Check if file already exists
                if dest_path.exists():
                    self.app.notify(f"File already exists: {dest_path.name}", severity="error")
                    return

                # Copy the file
                shutil.copy2(source_path, dest_path)
                self.app.notify(f"Imported: {source_path.name}", severity="success")

                # Refresh the tree
                self._do_refresh()
            except Exception as e:
                self.app.notify(f"Error importing file: {e}", severity="error")

    async def action_move_file(self) -> None:
        """Move the selected file to a new location."""
        if not self.selected_file:
            self.app.notify("Please select a file first", severity="warning")
            return

        if not self.selected_file.is_file():
            self.app.notify("Can only move files, not directories", severity="warning")
            return

        # Show move dialog
        dest_path_input = await self.app.push_screen_wait(MoveFileScreen(self.selected_file))

        if dest_path_input:
            try:
                dest_path = Path(dest_path_input)

                # If dest is a directory, append filename
                if dest_path.is_dir():
                    dest_path = dest_path / self.selected_file.name
                elif not dest_path.parent.exists():
                    self.app.notify(f"Destination directory does not exist", severity="error")
                    return

                # Check if destination already exists
                if dest_path.exists() and dest_path != self.selected_file:
                    self.app.notify(f"File already exists: {dest_path.name}", severity="error")
                    return

                # Move the file
                shutil.move(str(self.selected_file), str(dest_path))
                self.app.notify(f"Moved: {self.selected_file.name} → {dest_path.parent.name}/", severity="success")

                # Clear selection and refresh
                self.selected_file = None
                self._do_refresh()

                # Reset info panel
                info_widget = self.query_one("#file-info", Static)
                info_widget.update(self._get_welcome_message())
            except Exception as e:
                self.app.notify(f"Error moving file: {e}", severity="error")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
