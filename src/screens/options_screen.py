"""Options screen with keybindings and visual configuration."""

from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, TabbedContent, TabPane, DataTable
from textual.containers import Container, VerticalScroll
from textual.binding import Binding


class OptionsScreen(Screen):
    """Options screen with tabbed interface for configuration."""

    CSS = """
    OptionsScreen {
        align: center middle;
    }

    #options-container {
        width: 90%;
        height: 85%;
        border: thick $primary;
        background: $surface;
    }

    .options-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        background: $primary-darken-2;
        padding: 1;
        margin-bottom: 1;
    }

    TabbedContent {
        height: 100%;
    }

    TabPane {
        padding: 1 2;
    }

    DataTable {
        height: 100%;
        background: $surface;
    }

    .option-description {
        color: $text-muted;
        padding: 1 2;
        background: $boost;
        margin-bottom: 1;
    }

    .vim-config-info {
        color: $success;
        text-style: italic;
        padding: 1 2;
        border: solid $success;
        margin: 1 0;
    }

    .theme-preview {
        padding: 1 2;
        margin: 1 0;
        border: solid $primary;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close", show=True),
        Binding("q", "close", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Compose the options screen."""
        yield Header()

        with Container(id="options-container"):
            yield Static("⚙️  Options & Configuration", classes="options-title")

            with TabbedContent():
                # Keybindings Tab
                with TabPane("Keybindings", id="tab-keybindings"):
                    yield Static(
                        "Configure keyboard shortcuts. Press Enter on a binding to change it.",
                        classes="option-description"
                    )
                    yield DataTable(id="keybindings-table")

                # Visual Config Tab
                with TabPane("Visual", id="tab-visual"):
                    yield Static(
                        "Configure visual appearance and theme settings.",
                        classes="option-description"
                    )
                    yield self._get_vim_config_info()
                    yield DataTable(id="visual-table")

                # About Tab
                with TabPane("About", id="tab-about"):
                    yield self._get_about_content()

        yield Footer()

    def on_mount(self) -> None:
        """Initialize tables when screen mounts."""
        self._setup_keybindings_table()
        self._setup_visual_table()

    def _get_vim_config_info(self) -> Static:
        """Get vim configuration detection info."""
        vim_info = self._detect_vim_config()
        if vim_info:
            content = f"""[b green]✓ Vim config detected[/b green]

Theme: {vim_info.get('colorscheme', 'default')}
Background: {vim_info.get('background', 'dark')}

fftpeg will attempt to match your vim color scheme where possible."""
        else:
            content = """[dim]No vim config detected[/dim]

Using default theme. Set a colorscheme in ~/.vimrc or ~/.config/nvim/init.vim to sync themes."""

        return Static(content, classes="vim-config-info")

    def _detect_vim_config(self) -> dict:
        """Detect vim/neovim configuration."""
        vim_configs = [
            Path.home() / ".vimrc",
            Path.home() / ".config" / "nvim" / "init.vim",
            Path.home() / ".config" / "nvim" / "init.lua",
        ]

        for config_path in vim_configs:
            if config_path.exists():
                try:
                    content = config_path.read_text()
                    info = {}

                    # Parse colorscheme
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('colorscheme '):
                            info['colorscheme'] = line.split('colorscheme ')[1].strip()
                        elif 'set background=' in line:
                            info['background'] = line.split('set background=')[1].strip()

                    if info:
                        return info
                except Exception:
                    continue

        return None

    def _setup_keybindings_table(self) -> None:
        """Setup the keybindings table."""
        table = self.query_one("#keybindings-table", DataTable)
        table.add_columns("Key", "Action", "Description", "Category")
        table.cursor_type = "row"

        # Add keybindings from MainMenuScreen
        bindings = [
            ("U", "pull", "Download video from URL", "Download"),
            ("C", "convert", "Convert video format", "Video Ops"),
            ("P", "compress", "Compress video file", "Video Ops"),
            ("A", "audio", "Extract audio from video", "Audio"),
            ("T", "trim", "Trim/cut video", "Video Ops"),
            ("R", "refresh", "Refresh file list", "Navigation"),
            ("N", "rename", "Rename selected file", "File Ops"),
            ("D", "dedupe", "Find duplicate files", "File Ops"),
            ("F", "filter", "Cycle file type filters", "Navigation"),
            ("S", "settings", "Open settings", "System"),
            ("Q", "quit", "Quit application", "System"),
            ("↑/↓", "navigate", "Navigate file list", "Navigation"),
            ("Enter", "select", "Select/expand folder", "Navigation"),
            ("?", "help", "Show help", "System"),
        ]

        for key, action, desc, category in bindings:
            table.add_row(key, action, desc, category)

    def _setup_visual_table(self) -> None:
        """Setup the visual configuration table."""
        table = self.query_one("#visual-table", DataTable)
        table.add_columns("Setting", "Current Value", "Options")
        table.cursor_type = "row"

        # Detect system theme
        system_theme = self._detect_system_theme()
        vim_config = self._detect_vim_config()

        settings = [
            ("Theme", self._get_current_theme(system_theme, vim_config), "auto, dark, light, vim-sync"),
            ("Color Scheme", vim_config.get('colorscheme', 'default') if vim_config else 'default', "default, gruvbox, solarized, monokai, nord"),
            ("Border Style", "thick", "none, solid, dashed, thick, double"),
            ("Tree Style", "guides", "guides, none, simple"),
            ("Icon Set", "emoji", "emoji, ascii, nerd-fonts"),
            ("Font", "monospace", "monospace, system"),
            ("Line Numbers", "on", "on, off"),
            ("Highlight Current", "on", "on, off"),
        ]

        for setting, current, options in settings:
            table.add_row(setting, current, options)

    def _detect_system_theme(self) -> str:
        """Detect system theme (dark/light mode)."""
        # Try to detect from environment variables or system settings
        import subprocess
        import os

        # Check GTK theme (Linux)
        try:
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                theme = result.stdout.strip().strip("'")
                if "dark" in theme.lower():
                    return "dark"
                return "light"
        except Exception:
            pass

        # Check KDE plasma theme
        kde_config = Path.home() / ".config" / "kdeglobals"
        if kde_config.exists():
            try:
                content = kde_config.read_text()
                if "ColorScheme=Breeze Dark" in content or "dark" in content.lower():
                    return "dark"
            except Exception:
                pass

        # Check environment variable
        if os.environ.get("TERM") == "xterm-256color":
            # Default to dark for terminal
            return "dark"

        return "dark"  # Default

    def _get_current_theme(self, system_theme: str, vim_config: dict) -> str:
        """Get current theme based on system and vim config."""
        if vim_config and vim_config.get('colorscheme'):
            return f"vim-sync ({vim_config['colorscheme']})"
        return f"auto ({system_theme})"

    def _get_about_content(self) -> VerticalScroll:
        """Get about tab content."""
        content = Static("""[b cyan]fftpeg - Terminal FFmpeg[/b cyan]
[yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/yellow]

[b]Version:[/b] 0.1.0
[b]License:[/b] Apache 2.0

[yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/yellow]

[dim]A modern TUI and CLI for ffmpeg operations[/dim]

[b]Features:[/b]
• Download videos with yt-dlp
• Convert video formats
• Compress videos
• Extract audio
• Trim/cut videos
• Smart file organization
• Live file watching
• Configurable filters

[yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/yellow]

[b]Components:[/b]
• textual - TUI framework
• ffmpeg - Video processing
• yt-dlp - Video downloads
• watchdog - File monitoring

[yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/yellow]

[dim]Press ESC or Q to close[/dim]
""")
        return VerticalScroll(content)

    def action_close(self) -> None:
        """Close the options screen."""
        self.app.pop_screen()
