"""ASCII art and loading indicators for visual feedback."""

import random
from typing import List

# Collection of ASCII art for loading screens
LOADING_ARTS = {
    "film_reel": [
        "   ___  ",
        "  /   \\ ",
        " | (o) |",
        "  \\___/ ",
        "Processing..."
    ],
    "popcorn": [
        "    _~_    ",
        "   ( o )   ",
        "  ( o o )  ",
        " (  o o  ) ",
        " |_______|",
        "  Cooking..."
    ],
    "clapperboard": [
        " ________ ",
        "|__/__/__| ",
        "|  SCENE  |",
        "|  TAKE 1 |",
        "|_________|",
        "  Action!"
    ],
    "camera": [
        "   ___",
        "  [___]",
        "  |   |___",
        "  |___|   )",
        "   Recording..."
    ],
    "dots": [
        "",
        "  ⣾⣿⣿⣿",
        "  ⣿⣿⣿⣷",
        "  ⣿⣿⣿⣿",
        "  Loading..."
    ],
    "spinner": [
        "",
        "  ┃",
        "  ╱",
        "  ━",
        "  ╲",
        "  Working..."
    ],
    "blocks": [
        "",
        "  ▓▓▓▓▓▓▓▓▓▓",
        "  ▓▒▒▒▒▒▒▒▒▓",
        "  ▓▒░░░░░░▒▓",
        "  Processing..."
    ],
    "movie": [
        "  🎬",
        "  🎥",
        "  🎞️",
        "  📹",
        "  Creating..."
    ],
    "clock": [
        "   ___",
        "  /   \\",
        " | 3:00|",
        "  \\___/",
        "  Wait..."
    ],
    "download": [
        "    ↓",
        "   ↓↓↓",
        "  ↓↓↓↓↓",
        " ↓↓↓↓↓↓↓",
        "  Fetching..."
    ]
}


class LoadingIndicator:
    """Manages loading indicators and ASCII art."""

    def __init__(self, art_style: str = "random"):
        """Initialize loading indicator.

        Args:
            art_style: Style name or "random" for random selection
        """
        self.art_style = art_style
        self.current_art = None

    def get_art(self) -> List[str]:
        """Get ASCII art lines for loading screen.

        Returns:
            List of strings for ASCII art
        """
        if self.art_style == "random":
            art_name = random.choice(list(LOADING_ARTS.keys()))
        elif self.art_style in LOADING_ARTS:
            art_name = self.art_style
        else:
            # Fallback to simple spinner
            art_name = "spinner"

        self.current_art = art_name
        return LOADING_ARTS[art_name]

    def get_simple_text(self, message: str = "Loading") -> str:
        """Get simple loading text without ASCII art.

        Args:
            message: Loading message

        Returns:
            Formatted loading string
        """
        dots = "." * (random.randint(1, 3))
        return f"⏳ {message}{dots}"

    @staticmethod
    def get_available_styles() -> List[str]:
        """Get list of available art styles.

        Returns:
            List of style names
        """
        return ["random"] + list(LOADING_ARTS.keys())

    @staticmethod
    def format_art_for_display(art_lines: List[str]) -> str:
        """Format ASCII art lines for display in UI.

        Args:
            art_lines: List of art lines

        Returns:
            Formatted string with Rich markup
        """
        formatted = "\n".join(art_lines)
        return f"[cyan]{formatted}[/cyan]"
