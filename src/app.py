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
        loading_screen = LoadingScreen()
        self.push_screen(loading_screen)
        # Start initialization in background
        self.initialize_app(loading_screen)

    @work(exclusive=True)
    async def initialize_app(self, loading_screen: LoadingScreen) -> None:
        """Initialize the app asynchronously with progress updates.

        Args:
            loading_screen: Loading screen to update with progress
        """
        # Step 1: Initialize configuration (10%)
        loading_screen.update_progress(10, "Loading configuration...")
        await asyncio.sleep(0.1)

        # Step 2: Set up file paths (30%)
        loading_screen.update_progress(30, "Setting up file paths...")
        await asyncio.sleep(0.1)

        # Step 3: Initialize database (50%)
        loading_screen.update_progress(50, "Connecting to database...")
        await asyncio.sleep(0.1)

        # Step 4: Scan directory (70%)
        loading_screen.update_progress(70, "Scanning directory...")
        # This is where actual directory scanning happens
        await asyncio.sleep(0.2)

        # Step 5: Apply filters (90%)
        loading_screen.update_progress(90, "Applying filters...")
        await asyncio.sleep(0.1)

        # Step 6: Complete (100%)
        loading_screen.update_progress(100, "Ready!")
        await asyncio.sleep(0.2)

        # Pop loading screen and show main menu
        self.pop_screen()
        self.push_screen(MainMenuScreen(self.start_path))

    def action_help(self) -> None:
        """Show help screen."""
        # TODO: Implement help screen
        self.notify("Help screen coming soon!", severity="information")
