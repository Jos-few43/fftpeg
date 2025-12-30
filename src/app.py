"""Main Textual application for fftpeg."""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static
from screens.main_menu import MainMenuScreen


class FFTpegApp(App):
    """The main fftpeg TUI application."""

    CSS = """
    Screen {
        background: $surface;
    }

    #info-bar {
        dock: bottom;
        height: 1;
        background: $accent;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("question_mark", "help", "Help"),
    ]

    def __init__(self, start_path: Path):
        """Initialize the application.

        Args:
            start_path: The directory to start browsing from
        """
        super().__init__()
        self.start_path = start_path
        self.title = "fftpeg - Terminal FFmpeg"
        self.sub_title = f"📁 {start_path}"

    def on_mount(self) -> None:
        """Called when app starts."""
        self.push_screen(MainMenuScreen(self.start_path))

    def action_help(self) -> None:
        """Show help screen."""
        # TODO: Implement help screen
        self.notify("Help screen coming soon!", severity="information")
