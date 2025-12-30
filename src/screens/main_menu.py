"""Main menu screen with file browser."""

from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, DirectoryTree
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding


class VideoDirectoryTree(DirectoryTree):
    """A directory tree that filters for video files."""

    VIDEO_EXTENSIONS = {
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
        ".m4v", ".mpg", ".mpeg", ".3gp", ".ogv", ".ts", ".m2ts"
    }

    def filter_paths(self, paths):
        """Filter to show only directories and video files."""
        return [
            path for path in paths
            if path.is_dir() or path.suffix.lower() in self.VIDEO_EXTENSIONS
        ]


class MainMenuScreen(Screen):
    """The main menu screen with file browser."""

    CSS = """
    MainMenuScreen {
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 1fr;
    }

    #file-browser {
        border: solid $primary;
        height: 100%;
        padding: 1;
    }

    #info-panel {
        border: solid $secondary;
        height: 100%;
        padding: 1;
    }

    DirectoryTree {
        height: 100%;
    }

    .info-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .info-content {
        padding: 1 2;
    }

    .info-label {
        color: $text-muted;
        width: 15;
    }

    .info-value {
        color: $text;
    }
    """

    BINDINGS = [
        Binding("c", "convert", "Convert", show=True),
        Binding("p", "compress", "Compress", show=True),
        Binding("a", "audio", "Audio", show=True),
        Binding("t", "trim", "Trim", show=True),
        Binding("r", "rename", "Rename", show=False),
        Binding("d", "dedupe", "Dedupe", show=False),
        Binding("s", "settings", "Settings", show=False),
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

    def compose(self) -> ComposeResult:
        """Compose the main menu screen."""
        yield Header()

        with Container(id="file-browser"):
            yield Static("📁 File Browser", classes="info-title")
            yield VideoDirectoryTree(str(self.start_path))

        with Container(id="info-panel"):
            yield Static("ℹ️  File Information", classes="info-title")
            yield Static(
                "Select a video file to view details",
                id="file-info",
                classes="info-content"
            )

        yield Footer()

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

        info_text = f"""[b]{file_path.name}[/b]

Size:       {size_mb:.2f} MB
Format:     {file_path.suffix[1:].upper()}
Path:       {file_path.parent}

[dim]Press operation keys to process this file[/dim]
[dim]C=Convert  P=Compress  A=Audio  T=Trim[/dim]
"""

        info_widget.update(info_text)

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

    def action_rename(self) -> None:
        """Handle rename action."""
        self.app.notify("Rename feature coming soon!", severity="information")

    def action_dedupe(self) -> None:
        """Handle dedupe action."""
        self.app.notify("Dedupe feature coming soon!", severity="information")

    def action_settings(self) -> None:
        """Handle settings action."""
        self.app.notify("Settings coming soon!", severity="information")

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
