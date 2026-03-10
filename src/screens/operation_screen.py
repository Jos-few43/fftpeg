"""Generic operation screens for compress, convert, extract-audio, and trim."""

from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button, Select
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding

from ..cli import CLI


class OperationScreen(Screen):
    """Base screen for file operations."""

    CSS = """
    OperationScreen {
        align: center middle;
    }

    #op-container {
        width: 80;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }

    .op-title {
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
        min-height: 3;
    }

    .status-text { color: $text; }
    .success-text { color: $success; text-style: bold; }
    .error-text { color: $error; text-style: bold; }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    def action_cancel(self) -> None:
        self.app.pop_screen()


class CompressScreen(OperationScreen):
    """Screen for compressing video files."""

    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="op-container"):
            yield Static("🗜️  Compress Video", classes="op-title")
            with Vertical():
                yield Static(f"File: [cyan]{self.file_path.name}[/cyan]", classes="input-label")
                yield Static("Output file (leave empty for auto):", classes="input-label")
                yield Input(placeholder=f"{self.file_path.stem}_compressed{self.file_path.suffix}", id="output-input")
                yield Static("CRF (18=high quality, 28=small file):", classes="input-label")
                yield Input(value="23", id="crf-input")
                yield Static("Preset:", classes="input-label")
                yield Input(value="medium", id="preset-input")
                with Horizontal(classes="button-row"):
                    yield Button("Compress", variant="primary", id="run-btn")
                    yield Button("Cancel", variant="error", id="cancel-btn")
                yield Container(Static("Ready", classes="status-text"), id="status-box")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.action_cancel()
        elif event.button.id == "run-btn":
            self._run_compress()

    def _run_compress(self) -> None:
        status = self.query_one("#status-box", Container)
        output = self.query_one("#output-input", Input).value.strip() or None
        crf = int(self.query_one("#crf-input", Input).value.strip() or "23")
        preset = self.query_one("#preset-input", Input).value.strip() or "medium"

        status.update(Static("⏳ Compressing...", classes="status-text"))
        try:
            cli = CLI()
            result = cli.compress(str(self.file_path), output, crf=crf, preset=preset)
            if result == 0:
                status.update(Static("✅ Compression complete!", classes="success-text"))
            else:
                status.update(Static("❌ Compression failed", classes="error-text"))
        except Exception as e:
            status.update(Static(f"❌ Error: {e}", classes="error-text"))


class ConvertScreen(OperationScreen):
    """Screen for converting video format."""

    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="op-container"):
            yield Static("🎬 Convert Video", classes="op-title")
            with Vertical():
                yield Static(f"File: [cyan]{self.file_path.name}[/cyan]", classes="input-label")
                yield Static("Output file:", classes="input-label")
                yield Input(placeholder=f"{self.file_path.stem}.mkv", id="output-input")
                yield Static("Codec (leave empty for stream copy):", classes="input-label")
                yield Input(placeholder="copy, libx264, libx265", id="codec-input")
                with Horizontal(classes="button-row"):
                    yield Button("Convert", variant="primary", id="run-btn")
                    yield Button("Cancel", variant="error", id="cancel-btn")
                yield Container(Static("Ready", classes="status-text"), id="status-box")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.action_cancel()
        elif event.button.id == "run-btn":
            self._run_convert()

    def _run_convert(self) -> None:
        status = self.query_one("#status-box", Container)
        output = self.query_one("#output-input", Input).value.strip()
        codec = self.query_one("#codec-input", Input).value.strip() or None

        if not output:
            status.update(Static("❌ Please specify an output file", classes="error-text"))
            return

        status.update(Static("⏳ Converting...", classes="status-text"))
        try:
            cli = CLI()
            result = cli.convert(str(self.file_path), output, codec=codec)
            if result == 0:
                status.update(Static("✅ Conversion complete!", classes="success-text"))
            else:
                status.update(Static("❌ Conversion failed", classes="error-text"))
        except Exception as e:
            status.update(Static(f"❌ Error: {e}", classes="error-text"))


class AudioScreen(OperationScreen):
    """Screen for extracting audio from video."""

    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="op-container"):
            yield Static("🎵 Extract Audio", classes="op-title")
            with Vertical():
                yield Static(f"File: [cyan]{self.file_path.name}[/cyan]", classes="input-label")
                yield Static("Output file (leave empty for auto):", classes="input-label")
                yield Input(placeholder=f"{self.file_path.stem}.mp3", id="output-input")
                yield Static("Format (mp3, m4a, flac, wav):", classes="input-label")
                yield Input(value="mp3", id="format-input")
                yield Static("Quality/Bitrate:", classes="input-label")
                yield Input(value="320k", id="quality-input")
                with Horizontal(classes="button-row"):
                    yield Button("Extract", variant="primary", id="run-btn")
                    yield Button("Cancel", variant="error", id="cancel-btn")
                yield Container(Static("Ready", classes="status-text"), id="status-box")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.action_cancel()
        elif event.button.id == "run-btn":
            self._run_extract()

    def _run_extract(self) -> None:
        status = self.query_one("#status-box", Container)
        output = self.query_one("#output-input", Input).value.strip() or None
        fmt = self.query_one("#format-input", Input).value.strip() or "mp3"
        quality = self.query_one("#quality-input", Input).value.strip() or "320k"

        status.update(Static("⏳ Extracting audio...", classes="status-text"))
        try:
            cli = CLI()
            result = cli.extract_audio(str(self.file_path), output, format=fmt, quality=quality)
            if result == 0:
                status.update(Static("✅ Audio extraction complete!", classes="success-text"))
            else:
                status.update(Static("❌ Extraction failed", classes="error-text"))
        except Exception as e:
            status.update(Static(f"❌ Error: {e}", classes="error-text"))


class TrimScreen(OperationScreen):
    """Screen for trimming video."""

    def __init__(self, file_path: Path):
        super().__init__()
        self.file_path = file_path

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="op-container"):
            yield Static("✂️  Trim Video", classes="op-title")
            with Vertical():
                yield Static(f"File: [cyan]{self.file_path.name}[/cyan]", classes="input-label")
                yield Static("Output file (leave empty for auto):", classes="input-label")
                yield Input(placeholder=f"{self.file_path.stem}_trimmed{self.file_path.suffix}", id="output-input")
                yield Static("Start time (HH:MM:SS):", classes="input-label")
                yield Input(value="00:00:00", id="start-input")
                yield Static("End time (HH:MM:SS, leave empty to use duration):", classes="input-label")
                yield Input(placeholder="00:01:30", id="end-input")
                yield Static("Duration (HH:MM:SS, alternative to end time):", classes="input-label")
                yield Input(placeholder="00:00:30", id="duration-input")
                with Horizontal(classes="button-row"):
                    yield Button("Trim", variant="primary", id="run-btn")
                    yield Button("Cancel", variant="error", id="cancel-btn")
                yield Container(Static("Ready", classes="status-text"), id="status-box")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-btn":
            self.action_cancel()
        elif event.button.id == "run-btn":
            self._run_trim()

    def _run_trim(self) -> None:
        status = self.query_one("#status-box", Container)
        output = self.query_one("#output-input", Input).value.strip() or None
        start = self.query_one("#start-input", Input).value.strip() or "00:00:00"
        end = self.query_one("#end-input", Input).value.strip() or None
        duration = self.query_one("#duration-input", Input).value.strip() or None

        status.update(Static("⏳ Trimming...", classes="status-text"))
        try:
            cli = CLI()
            result = cli.trim(str(self.file_path), output, start=start, end=end, duration=duration)
            if result == 0:
                status.update(Static("✅ Trim complete!", classes="success-text"))
            else:
                status.update(Static("❌ Trim failed", classes="error-text"))
        except Exception as e:
            status.update(Static(f"❌ Error: {e}", classes="error-text"))
