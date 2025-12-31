"""Loading splash screen with progress indication."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Center, Vertical
from textual.reactive import reactive

from ..utils.loading_art import LoadingIndicator


class LoadingScreen(Screen):
    """Splash screen shown during app initialization with progress."""

    CSS = """
    LoadingScreen {
        align: center middle;
        background: $surface;
    }

    #loading-container {
        width: auto;
        height: auto;
        align: center middle;
    }

    #progress-bar {
        text-align: center;
        color: $accent;
        margin: 2;
        min-width: 60;
    }

    #loading-message {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }

    #app-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 2;
    }
    """

    progress = reactive(0)
    status = reactive("Initializing...")

    def __init__(self, animation_style: str = "random"):
        """Initialize loading screen.

        Args:
            animation_style: Progress animation style to use
        """
        super().__init__()
        self.animation_style = animation_style
        self.indicator = LoadingIndicator(animation_style)

    def compose(self) -> ComposeResult:
        """Compose the loading screen."""
        with Center():
            with Vertical(id="loading-container"):
                yield Static("🎬 fftpeg", id="app-title")
                yield Static("", id="progress-bar")
                yield Static(self.status, id="loading-message")

    def watch_progress(self, progress: int) -> None:
        """Update progress bar when progress changes."""
        try:
            progress_widget = self.query_one("#progress-bar", Static)
            frame = self.indicator.get_progress_frame(progress)
            progress_widget.update(frame)
        except Exception:
            pass

    def watch_status(self, status: str) -> None:
        """Update status message when it changes."""
        try:
            message_widget = self.query_one("#loading-message", Static)
            message_widget.update(status)
        except Exception:
            pass

    def update_progress(self, percent: int, task: str = "") -> None:
        """Update progress and status.

        Args:
            percent: Progress percentage (0-100)
            task: Current task description
        """
        self.progress = percent
        if task:
            self.status = task
