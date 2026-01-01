"""Options screen with keybindings and visual configuration."""

from pathlib import Path
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, TabbedContent, TabPane, DataTable, Select
from textual.containers import Container, VerticalScroll, Horizontal
from textual.binding import Binding
from ..utils.theme_detector import get_theme, get_available_themes, get_theme_colors


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
                    yield self._get_theme_switcher()
                    yield DataTable(id="visual-table")

                # About Tab
                with TabPane("About", id="tab-about"):
                    yield self._get_about_content()

        yield Footer()

    def on_mount(self) -> None:
        """Initialize tables when screen mounts."""
        self._setup_keybindings_table()
        self._setup_visual_table()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in tables."""
        table = event.data_table

        # Get the table ID to determine which table was clicked
        if table.id == "visual-table":
            row_key = event.row_key
            row_data = table.get_row(row_key)
            setting_name = str(row_data[0])

            if "Theme" in setting_name:
                self.app.notify(
                    "Theme changes require restart. Edit your vim config or modify theme_detector.py",
                    severity="information"
                )
            else:
                self.app.notify(
                    f"Selected: {setting_name} (configuration coming soon)",
                    severity="information"
                )
        elif table.id == "keybindings-table":
            row_key = event.row_key
            row_data = table.get_row(row_key)
            key = str(row_data[0])
            action = str(row_data[1])
            self.app.notify(
                f"Keybinding: {key} → {action}",
                severity="information"
            )

    def _get_vim_config_info(self) -> Static:
        """Get vim configuration detection info."""
        detected_theme = get_theme()
        available_themes = get_available_themes()

        if detected_theme and detected_theme in available_themes:
            content = f"""[b green]✓ Vim/Neovim theme detected: {detected_theme}[/b green]

Auto-syncing colors from your editor config.
Theme colors are applied automatically on startup.

To change themes manually, use the theme selector below."""
        else:
            content = f"""[b yellow]⚙ Using default theme: {detected_theme}[/b yellow]

Set a colorscheme in ~/.config/nvim/lua/plugins/theme.lua to auto-sync themes.

Or use the theme selector below to choose manually."""

        return Static(content, classes="vim-config-info")

    def _get_theme_switcher(self) -> Container:
        """Get theme switcher widget."""
        available_themes = get_available_themes()
        current_theme = getattr(self.app, 'theme_name', get_theme())

        container = Container(id="theme-switcher")

        # Create theme preview
        theme_info = Static(f"""[b]Current Theme:[/b] {current_theme}

[dim]Available themes: {', '.join(available_themes)}[/dim]

Select a theme below to preview and apply:
""", classes="theme-preview")

        # Note: Select widget requires options as tuples
        theme_options = [(theme.title(), theme) for theme in available_themes]

        return Static("""[b]Theme Switcher:[/b]

Use arrow keys to browse themes in the table below.
Press Enter to apply a new theme (restart required).
""", classes="theme-preview")

    def _setup_keybindings_table(self) -> None:
        """Setup the keybindings table."""
        table = self.query_one("#keybindings-table", DataTable)
        table.add_columns("Key", "Action", "Description", "Category")
        table.cursor_type = "row"

        # Add keybindings from MainMenuScreen
        bindings = [
            ("U", "pull", "Download video from URL", "Download"),
            ("I", "import", "Import file from path", "File Ops"),
            ("M", "move", "Move file to new location", "File Ops"),
            ("Del", "delete", "Delete selected file", "File Ops"),
            ("C", "convert", "Convert video format", "Video Ops"),
            ("P", "compress", "Compress video file", "Video Ops"),
            ("A", "audio", "Extract audio from video", "Audio"),
            ("T", "trim", "Trim/cut video", "Video Ops"),
            ("R", "refresh", "Refresh file list", "Navigation"),
            ("N", "rename", "Rename selected file", "File Ops"),
            ("D", "dedupe", "Find duplicate files", "File Ops"),
            ("F", "filter", "Cycle file type filters", "Navigation"),
            ("H", "toggle_hidden", "Toggle hidden files", "Navigation"),
            ("Ctrl+F", "toggle_filter", "Toggle filter on/off", "Navigation"),
            ("O", "options", "Open options", "System"),
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

        # Get current theme
        current_theme = getattr(self.app, 'theme_name', get_theme())
        available_themes = get_available_themes()

        settings = [
            ("Color Theme", current_theme, ", ".join(available_themes)),
            ("Theme Source", "vim-sync" if current_theme == get_theme() else "manual", "vim-sync, manual"),
            ("Border Style", "thick", "none, solid, dashed, thick, double"),
            ("Tree Style", "guides", "guides, none, simple"),
            ("Icon Set", "emoji", "emoji, ascii, nerd-fonts"),
            ("Font", "monospace", "monospace, system"),
            ("Line Numbers", "on", "on, off"),
            ("Highlight Current", "on", "on, off"),
        ]

        for setting, current, options in settings:
            table.add_row(setting, current, options)

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
