"""Theme detection from vim/neovim configuration."""

import re
from pathlib import Path
from typing import Optional, Dict, Tuple

# Theme color mappings for popular vim themes
THEME_COLORS = {
    "hackerman": {
        "primary": "#00ff00",
        "secondary": "#00cc00",
        "accent": "#00ff00",
        "warning": "#ffff00",
        "error": "#ff0000",
        "success": "#00ff00",
        "background": "#000000",
        "surface": "#0a0a0a",
        "boost": "#0f0f0f",
        "text": "#00ff00",
        "text-muted": "#008800",
    },
    "catppuccin-mocha": {
        "primary": "#89b4fa",
        "secondary": "#cba6f7",
        "accent": "#f5c2e7",
        "warning": "#f9e2af",
        "error": "#f38ba8",
        "success": "#a6e3a1",
        "background": "#1e1e2e",
        "surface": "#181825",
        "boost": "#313244",
        "text": "#cdd6f4",
        "text-muted": "#6c7086",
    },
    "gruvbox": {
        "primary": "#83a598",
        "secondary": "#d3869b",
        "accent": "#fabd2f",
        "warning": "#fabd2f",
        "error": "#fb4934",
        "success": "#b8bb26",
        "background": "#282828",
        "surface": "#1d2021",
        "boost": "#3c3836",
        "text": "#ebdbb2",
        "text-muted": "#928374",
    },
    "nord": {
        "primary": "#88c0d0",
        "secondary": "#81a1c1",
        "accent": "#8fbcbb",
        "warning": "#ebcb8b",
        "error": "#bf616a",
        "success": "#a3be8c",
        "background": "#2e3440",
        "surface": "#3b4252",
        "boost": "#434c5e",
        "text": "#eceff4",
        "text-muted": "#4c566a",
    },
    "tokyonight": {
        "primary": "#7aa2f7",
        "secondary": "#bb9af7",
        "accent": "#9ece6a",
        "warning": "#e0af68",
        "error": "#f7768e",
        "success": "#9ece6a",
        "background": "#1a1b26",
        "surface": "#16161e",
        "boost": "#24283b",
        "text": "#c0caf5",
        "text-muted": "#565f89",
    },
    "dracula": {
        "primary": "#bd93f9",
        "secondary": "#ff79c6",
        "accent": "#8be9fd",
        "warning": "#ffb86c",
        "error": "#ff5555",
        "success": "#50fa7b",
        "background": "#282a36",
        "surface": "#21222c",
        "boost": "#343746",
        "text": "#f8f8f2",
        "text-muted": "#6272a4",
    },
    "onedark": {
        "primary": "#61afef",
        "secondary": "#c678dd",
        "accent": "#56b6c2",
        "warning": "#e5c07b",
        "error": "#e06c75",
        "success": "#98c379",
        "background": "#282c34",
        "surface": "#21252b",
        "boost": "#2c313c",
        "text": "#abb2bf",
        "text-muted": "#5c6370",
    },
    "solarized-dark": {
        "primary": "#268bd2",
        "secondary": "#6c71c4",
        "accent": "#2aa198",
        "warning": "#b58900",
        "error": "#dc322f",
        "success": "#859900",
        "background": "#002b36",
        "surface": "#073642",
        "boost": "#586e75",
        "text": "#839496",
        "text-muted": "#657b83",
    },
}

# Default fallback theme (hackerman - user's current theme)
DEFAULT_THEME = "hackerman"


def detect_nvim_theme() -> Optional[str]:
    """Detect the current neovim colorscheme.

    Returns:
        Theme name if detected, None otherwise
    """
    # Check neovim config locations
    config_paths = [
        Path.home() / ".config" / "nvim" / "lua" / "plugins" / "theme.lua",
        Path.home() / ".config" / "nvim" / "init.lua",
        Path.home() / ".config" / "nvim" / "init.vim",
    ]

    for config_path in config_paths:
        if not config_path.exists():
            continue

        try:
            content = config_path.read_text()

            # Look for colorscheme setting in Lua
            lua_match = re.search(r'colorscheme\s*=\s*["\']([^"\']+)["\']', content)
            if lua_match:
                return normalize_theme_name(lua_match.group(1))

            # Look for colorscheme command in Vim script
            vim_match = re.search(r'colorscheme\s+(\S+)', content)
            if vim_match:
                return normalize_theme_name(vim_match.group(1))

        except Exception:
            continue

    return None


def detect_vim_theme() -> Optional[str]:
    """Detect the current vim colorscheme.

    Returns:
        Theme name if detected, None otherwise
    """
    vimrc_paths = [
        Path.home() / ".vimrc",
        Path.home() / ".vim" / "vimrc",
    ]

    for vimrc_path in vimrc_paths:
        if not vimrc_path.exists():
            continue

        try:
            content = vimrc_path.read_text()
            match = re.search(r'colorscheme\s+(\S+)', content)
            if match:
                return normalize_theme_name(match.group(1))
        except Exception:
            continue

    return None


def normalize_theme_name(theme: str) -> str:
    """Normalize theme name to match our theme database.

    Args:
        theme: Raw theme name from config

    Returns:
        Normalized theme name
    """
    theme = theme.lower().strip()

    # Handle common variations
    theme_map = {
        "catppuccin": "catppuccin-mocha",
        "gruvbox-material": "gruvbox",
        "nord.nvim": "nord",
        "tokyonight.nvim": "tokyonight",
        "tokyonight-night": "tokyonight",
        "onedark.nvim": "onedark",
        "solarized": "solarized-dark",
    }

    return theme_map.get(theme, theme)


def get_theme() -> str:
    """Get the user's theme from vim/neovim config.

    Returns:
        Theme name (defaults to hackerman if not detected)
    """
    # Try neovim first (more common)
    theme = detect_nvim_theme()
    if theme and theme in THEME_COLORS:
        return theme

    # Fall back to vim
    theme = detect_vim_theme()
    if theme and theme in THEME_COLORS:
        return theme

    # Return default
    return DEFAULT_THEME


def get_theme_colors(theme_name: Optional[str] = None) -> Dict[str, str]:
    """Get color palette for a theme.

    Args:
        theme_name: Theme name (auto-detects if None)

    Returns:
        Dictionary of color variables
    """
    if theme_name is None:
        theme_name = get_theme()

    if theme_name not in THEME_COLORS:
        theme_name = DEFAULT_THEME

    return THEME_COLORS[theme_name]


def generate_textual_css(theme_name: Optional[str] = None) -> str:
    """Generate Textual CSS variables for a theme.

    Args:
        theme_name: Theme name (auto-detects if None)

    Returns:
        CSS string with theme variables
    """
    colors = get_theme_colors(theme_name)

    css_lines = []
    for key, value in colors.items():
        css_lines.append(f"    ${key}: {value};")

    return "\n".join(css_lines)


def get_available_themes() -> list[str]:
    """Get list of available theme names.

    Returns:
        List of theme names
    """
    return sorted(THEME_COLORS.keys())
