"""Main Textual application for fftpeg."""

from pathlib import Path
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Static
from textual import work
from .screens.main_menu import MainMenuScreen
from .screens.loading_screen import LoadingScreen
from .utils.theme_detector import get_theme, get_theme_colors, generate_textual_css
import asyncio


class FFTpegApp(App):
    """The main fftpeg TUI application."""

    # Detect theme before class initialization
    _detected_theme = get_theme()
    _theme_colors = get_theme_colors(_detected_theme)

    # Comprehensive CSS - override all Textual defaults with theme colors
    CSS = """
    * {
        scrollbar-background: $surface;
        scrollbar-color: $primary;
        scrollbar-color-hover: $accent;
        scrollbar-color-active: $accent;
        link-background: transparent;
        link-color: $primary;
        link-style: underline;
        link-background-hover: $surface;
        link-color-hover: $accent;
        link-style-hover: bold;
    }

    Screen {
        background: $background;
    }

    Header {
        background: $primary;
        color: $text;
    }

    Footer {
        background: $surface;
        color: $text;
    }

    Footer > .footer--highlight {
        background: $primary;
    }

    Footer > .footer--highlight-key {
        background: $accent;
        color: $background;
    }

    Footer > .footer--key {
        background: $surface;
        color: $text;
    }

    Button {
        background: $primary;
        color: $background;
        border: none;
    }

    Button:hover {
        background: $accent;
        color: $background;
    }

    Button:focus {
        background: $accent;
        color: $background;
    }

    Button.-primary {
        background: $primary;
        color: $background;
    }

    Button.-primary:hover {
        background: $accent;
    }

    Button.-warning {
        background: $warning;
        color: $background;
    }

    Button.-warning:hover {
        background: $accent;
    }

    Button.-error {
        background: $error;
        color: $background;
    }

    Button.-error:hover {
        background: $warning;
    }

    Input {
        background: $surface;
        color: $text;
        border: solid $primary;
    }

    Input:focus {
        border: solid $accent;
    }

    Input > .input--cursor {
        background: $accent;
        color: $background;
    }

    Input > .input--placeholder {
        color: $text-muted;
    }

    DirectoryTree {
        background: $background;
        color: $text;
    }

    DirectoryTree > .directory-tree--folder {
        color: $primary;
    }

    DirectoryTree > .directory-tree--file {
        color: $text;
    }

    DirectoryTree > .directory-tree--cursor {
        background: $primary;
        color: $background;
    }

    DirectoryTree > .directory-tree--highlight {
        background: $surface;
    }

    Tree {
        background: $background;
        color: $text;
    }

    Tree > .tree--cursor {
        background: $primary;
        color: $background;
    }

    Tree > .tree--highlight {
        background: $surface;
    }

    DataTable {
        background: $background;
        color: $text;
    }

    DataTable > .datatable--cursor {
        background: $primary;
        color: $background;
    }

    DataTable > .datatable--header {
        background: $surface;
        color: $accent;
        text-style: bold;
    }

    DataTable > .datatable--odd-row {
        background: $background;
    }

    DataTable > .datatable--even-row {
        background: $surface;
    }

    DataTable > .datatable--hover {
        background: $boost;
    }

    Label {
        color: $text;
    }

    Static {
        color: $text;
    }

    Container {
        background: $background;
    }

    TabbedContent {
        background: $background;
    }

    TabbedContent > ContentSwitcher {
        background: $background;
    }

    Tabs {
        background: $surface;
    }

    Tab {
        background: $surface;
        color: $text-muted;
    }

    Tab:hover {
        background: $boost;
        color: $text;
    }

    Tab.-active {
        background: $primary;
        color: $background;
    }

    ProgressBar {
        background: $surface;
    }

    ProgressBar > .bar--bar {
        color: $primary;
    }

    ProgressBar > .bar--complete {
        color: $success;
    }

    ProgressBar > .bar--indeterminate {
        color: $accent;
    }

    #info-bar {
        dock: bottom;
        height: 1;
        background: $accent;
        color: $background;
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

        # Store theme info
        self.theme_name = self._detected_theme
        self.theme_colors = self._theme_colors

    def get_css_variables(self):
        """Override to provide theme colors as CSS variables."""
        # Get default variables
        variables = super().get_css_variables()

        # Override with theme colors
        variables.update({
            "primary": self._theme_colors['primary'],
            "secondary": self._theme_colors['secondary'],
            "accent": self._theme_colors['accent'],
            "warning": self._theme_colors['warning'],
            "error": self._theme_colors['error'],
            "success": self._theme_colors['success'],
            "background": self._theme_colors['background'],
            "surface": self._theme_colors['surface'],
            "boost": self._theme_colors['boost'],
            "text": self._theme_colors['text'],
            "text-muted": self._theme_colors['text-muted'],
            # Derived colors
            "primary-background": self._theme_colors['primary'],
            "primary-lighten-1": self._theme_colors['accent'],
            "primary-lighten-2": self._theme_colors['accent'],
            "primary-darken-1": self._theme_colors['surface'],
            "primary-darken-2": self._theme_colors['surface'],
            "primary-darken-3": self._theme_colors['background'],
            "secondary-background": self._theme_colors['secondary'],
            "panel": self._theme_colors['surface'],
        })

        return variables

    def on_mount(self) -> None:
        """Called when app starts."""
        # Start initialization
        self.initialize_app()

    @work(exclusive=True)
    async def initialize_app(self) -> None:
        """Initialize the app asynchronously with progress updates."""
        # Show loading screen
        loading_screen = LoadingScreen()
        self.push_screen(loading_screen)

        # Give UI time to render
        await asyncio.sleep(0.02)

        # Smooth progress animation with more granular steps
        tasks = [
            (0, 15, "Loading configuration...", 0.08),
            (15, 35, "Setting up file paths...", 0.08),
            (35, 60, "Connecting to database...", 0.08),
            (60, 85, "Scanning directory...", 0.12),
            (85, 95, "Applying filters...", 0.06),
            (95, 100, "Ready!", 0.06),
        ]

        for start, end, task, duration in tasks:
            loading_screen.update_progress(start, task)
            # Smooth animation within this range
            steps = end - start
            step_delay = duration / steps if steps > 0 else 0.01

            for i in range(start + 1, end + 1):
                loading_screen.update_progress(i, task)
                await asyncio.sleep(step_delay)

        # Brief pause at 100%
        await asyncio.sleep(0.1)

        # Auto-transition to main menu
        self.pop_screen()
        self.push_screen(MainMenuScreen(self.start_path))

    def action_help(self) -> None:
        """Show help screen."""
        # TODO: Implement help screen
        self.notify("Help screen coming soon!", severity="information")
