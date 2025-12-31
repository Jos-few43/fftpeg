"""Main Textual application for fftpeg."""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static
from textual import work
from .screens.main_menu import MainMenuScreen
from .screens.loading_screen import LoadingScreen
import asyncio


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
        # Show loading screen first
        self.push_screen(LoadingScreen())
        # Start initialization in background
        self.initialize_app()

    @work(exclusive=True)
    async def initialize_app(self) -> None:
        """Initialize the app asynchronously."""
        # Simulate initialization time (can be replaced with actual loading tasks)
        await asyncio.sleep(1.5)

        # Pop loading screen and show main menu
        self.pop_screen()
        self.push_screen(MainMenuScreen(self.start_path))

    def action_help(self) -> None:
        """Show help screen."""
        # TODO: Implement help screen
        self.notify("Help screen coming soon!", severity="information")
