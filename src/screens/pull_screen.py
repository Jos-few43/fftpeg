"""Pull/download screen for downloading videos from URLs."""

from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button, Label, ProgressBar
from textual.containers import Container, Vertical, Horizontal, Center
from textual.binding import Binding

from ..utils.downloader import VideoDownloader
from ..utils.database import Database
from ..utils.symlink_manager import SymlinkManager
from ..config.settings import Config


class PullScreen(Screen):
    """Screen for downloading videos from URLs."""

    CSS = """
    PullScreen {
        align: center middle;
    }

    #pull-container {
        width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }

    .pull-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
        background: $primary-darken-2;
        padding: 1;
    }

    .input-label {
        color: $text-muted;
        margin-top: 1;
        margin-bottom: 1;
    }

    Input {
        margin-bottom: 1;
    }

    #url-input {
        width: 100%;
    }

    #tags-input {
        width: 100%;
    }

    .button-row {
        layout: horizontal;
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }

    #status-box {
        border: solid $secondary;
        padding: 1;
        margin-top: 1;
        height: auto;
        min-height: 5;
    }

    .status-text {
        color: $text;
    }

    .success-text {
        color: $success;
        text-style: bold;
    }

    .error-text {
        color: $error;
        text-style: bold;
    }

    .info-box {
        border: solid $accent;
        background: $boost;
        padding: 1;
        margin: 1 0;
    }

    ProgressBar {
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def __init__(self):
        """Initialize pull screen."""
        super().__init__()
        self.config = Config()
        self.db = Database()

        # Get base path from config
        org_paths = self.config.get_organization_paths()
        base_path = org_paths['base'].parent

        self.symlink_manager = SymlinkManager(base_path)
        self.downloader = VideoDownloader(self.config, self.db, self.symlink_manager)

    def compose(self) -> ComposeResult:
        """Compose the pull screen."""
        yield Header()

        with Container(id="pull-container"):
            yield Static("📥 Pull Video from URL", classes="pull-title")

            with Vertical():
                yield Static("Enter video URL:", classes="input-label")
                yield Input(
                    placeholder="https://www.youtube.com/watch?v=...",
                    id="url-input"
                )

                yield Static(
                    "Additional tags (comma-separated, optional):",
                    classes="input-label"
                )
                yield Input(
                    placeholder="tutorial, archive, music",
                    id="tags-input"
                )

                yield Static(
                    "Auto-tags will be applied based on source (e.g., 'youtube' for YouTube videos)",
                    classes="info-box"
                )

                with Horizontal(classes="button-row"):
                    yield Button("Download", variant="primary", id="download-btn")
                    yield Button("Preview Info", variant="default", id="preview-btn")
                    yield Button("Cancel", variant="error", id="cancel-btn")

                yield Container(
                    Static("Ready to download", classes="status-text"),
                    id="status-box"
                )

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "download-btn":
            self.action_download()
        elif event.button.id == "preview-btn":
            self.action_preview()
        elif event.button.id == "cancel-btn":
            self.action_cancel()

    def action_download(self) -> None:
        """Start download process."""
        url_input = self.query_one("#url-input", Input)
        tags_input = self.query_one("#tags-input", Input)
        status_box = self.query_one("#status-box", Container)

        url = url_input.value.strip()
        if not url:
            status_box.update(Static("❌ Please enter a URL", classes="error-text"))
            return

        # Parse additional tags
        tags_str = tags_input.value.strip()
        additional_tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []

        # Update status
        status_box.update(Static("⏳ Downloading...", classes="status-text"))

        # Progress callback
        def progress_callback(progress_data):
            if 'downloaded_bytes' in progress_data and 'total_bytes' in progress_data:
                percent = (progress_data['downloaded_bytes'] / progress_data['total_bytes']) * 100
                status_box.update(
                    Static(f"⏳ Downloading... {percent:.1f}%", classes="status-text")
                )

        # Download
        try:
            result = self.downloader.download(url, progress_callback, additional_tags)

            if result['status'] == 'success':
                message = f"""✅ Download complete!

[green]File:[/green] {result['filepath'].name}
[green]Source:[/green] {result['source']}
[green]Tags:[/green] {', '.join(result['tags'])}
[green]Size:[/green] {result['metadata']['size'] / (1024*1024):.1f} MB

File organized in:
  • downloads/
  • by-source/{result['source']}/
  • by-tag/... (for each tag)
  • by-date/...
"""
                status_box.update(Static(message, classes="success-text"))

            elif result['status'] == 'exists':
                status_box.update(
                    Static(f"ℹ️  URL already downloaded:\n{result['file']['filepath']}", classes="status-text")
                )

            elif result['status'] == 'duplicate':
                status_box.update(
                    Static(f"ℹ️  Duplicate file detected:\n{result['file']['filepath']}", classes="status-text")
                )

            else:
                status_box.update(
                    Static(f"❌ Error: {result['message']}", classes="error-text")
                )

        except Exception as e:
            status_box.update(
                Static(f"❌ Unexpected error: {str(e)}", classes="error-text")
            )

    def action_preview(self) -> None:
        """Preview video information without downloading."""
        url_input = self.query_one("#url-input", Input)
        status_box = self.query_one("#status-box", Container)

        url = url_input.value.strip()
        if not url:
            status_box.update(Static("❌ Please enter a URL", classes="error-text"))
            return

        status_box.update(Static("⏳ Fetching video info...", classes="status-text"))

        try:
            info = self.downloader.get_video_info(url)

            if info:
                duration_str = f"{int(info['duration'] // 60)}:{int(info['duration'] % 60):02d}" if info.get('duration') else "Unknown"
                views_str = f"{info.get('view_count', 0):,}" if info.get('view_count') else "Unknown"

                message = f"""ℹ️  Video Information:

[cyan]Title:[/cyan] {info.get('title', 'Unknown')}
[cyan]Uploader:[/cyan] {info.get('uploader', 'Unknown')}
[cyan]Duration:[/cyan] {duration_str}
[cyan]Views:[/cyan] {views_str}

Ready to download!
"""
                status_box.update(Static(message, classes="status-text"))
            else:
                status_box.update(
                    Static("❌ Could not fetch video info", classes="error-text")
                )

        except Exception as e:
            status_box.update(
                Static(f"❌ Error: {str(e)}", classes="error-text")
            )

    def action_cancel(self) -> None:
        """Cancel and return to main screen."""
        self.app.pop_screen()
