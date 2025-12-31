"""Loading splash screen with ASCII art."""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static
from textual.containers import Center, Vertical
from textual import work
import asyncio

from ..utils.loading_art import LoadingIndicator


class LoadingScreen(Screen):
    """Splash screen shown during app initialization."""

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

    #ascii-art {
        text-align: center;
        color: $accent;
        margin: 2;
    }

    #loading-message {
        text-align: center;
        color: $text-muted;
        text-style: italic;
        margin-top: 1;
    }

    #app-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 2;
    }
    """

    def __init__(self, art_style: str = "random"):
        """Initialize loading screen.

        Args:
            art_style: ASCII art style to use
        """
        super().__init__()
        self.art_style = art_style
        self.indicator = LoadingIndicator(art_style)

    def compose(self) -> ComposeResult:
        """Compose the loading screen."""
        art_lines = self.indicator.get_art()
        art_text = "\n".join(art_lines[:-1])  # All lines except last (which is message)
        message = art_lines[-1] if art_lines else "Loading..."

        with Center():
            with Vertical(id="loading-container"):
                yield Static("🎬 fftpeg", id="app-title")
                yield Static(art_text, id="ascii-art")
                yield Static(message, id="loading-message")

    def on_mount(self) -> None:
        """Start animation when mounted."""
        self.animate_loading()

    @work(exclusive=True)
    async def animate_loading(self) -> None:
        """Animate the loading screen."""
        message_widget = self.query_one("#loading-message", Static)
        art_widget = self.query_one("#ascii-art", Static)

        # Cycle through a few animations
        for _ in range(3):
            for dots in [".", "..", "..."]:
                if not self.is_mounted:
                    return
                art_lines = self.indicator.get_art()
                base_message = art_lines[-1] if art_lines else "Loading"
                message_widget.update(f"{base_message}{dots}")
                await asyncio.sleep(0.3)

    def finish_loading(self) -> None:
        """Mark loading as complete and transition."""
        # This will be called by the app when ready
        pass
