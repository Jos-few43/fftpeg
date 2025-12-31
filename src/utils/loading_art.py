"""ASCII art and loading indicators for visual feedback."""

import random
from typing import List, Callable

# Collection of ASCII progress animations
PROGRESS_ANIMATIONS = {
    "bar": {
        "name": "Progress Bar",
        "frames": lambda percent: f"[{'='*int(percent/5)}{'·'*(20-int(percent/5))}] {percent}%"
    },
    "blocks": {
        "name": "Block Builder",
        "frames": lambda percent: ''.join(['█' if i < percent/5 else '░' for i in range(20)])
    },
    "dots": {
        "name": "Growing Dots",
        "frames": lambda percent: '·' * int(percent/5)
    },
    "arrows": {
        "name": "Arrow Progress",
        "frames": lambda percent: '>' * int(percent/10) + '-' * (10 - int(percent/10))
    },
    "film_strip": {
        "name": "Film Strip",
        "frames": lambda percent: '|' + ('▓' * int(percent/5)) + ('░' * (20 - int(percent/5))) + '|'
    },
    "wave": {
        "name": "Wave",
        "frames": lambda percent: ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'][int(percent/10) % 10]
    },
    "spinner": {
        "name": "Spinner",
        "frames": lambda percent: ['|', '/', '-', '\\'][int(percent/10) % 4]
    },
    "dots_pulse": {
        "name": "Pulsing Dots",
        "frames": lambda percent: '⠿⠿⠿⠿⠿⠿⠿⠿⠿⠿'[:int(percent/10)]
    },
    "building": {
        "name": "Building Up",
        "frames": lambda percent: '\n'.join(['█' * 20 for _ in range(int(percent/20))])
    },
    "loading_bar": {
        "name": "Classic Loading",
        "frames": lambda percent: f"Loading {'.' * (int(percent/20) % 4)}{' ' * (3 - int(percent/20) % 4)} [{percent:3d}%]"
    }
}


class LoadingIndicator:
    """Manages loading indicators and progress animations."""

    def __init__(self, animation_style: str = "random"):
        """Initialize loading indicator.

        Args:
            animation_style: Animation style name or "random" for random selection
        """
        self.animation_style = animation_style
        self.current_style = None

    def get_progress_frame(self, percent: int) -> str:
        """Get progress animation frame for current percentage.

        Args:
            percent: Progress percentage (0-100)

        Returns:
            Formatted progress string
        """
        # Select animation style on first call
        if not self.current_style:
            if self.animation_style == "random":
                self.current_style = random.choice(list(PROGRESS_ANIMATIONS.keys()))
            elif self.animation_style in PROGRESS_ANIMATIONS:
                self.current_style = self.animation_style
            else:
                # Fallback to progress bar
                self.current_style = "bar"

        animation = PROGRESS_ANIMATIONS[self.current_style]
        return animation["frames"](percent)

    def get_status_message(self, task: str, percent: int) -> str:
        """Get formatted status message with task and progress.

        Args:
            task: Current task description
            percent: Progress percentage

        Returns:
            Formatted status string
        """
        return f"{task}: {percent}%"

    @staticmethod
    def get_available_animations() -> List[str]:
        """Get list of available animation styles.

        Returns:
            List of animation names
        """
        return ["random"] + list(PROGRESS_ANIMATIONS.keys())

    @staticmethod
    def get_animation_preview(style: str, percent: int = 50) -> str:
        """Get preview of an animation style.

        Args:
            style: Animation style name
            percent: Percentage to preview at

        Returns:
            Preview string
        """
        if style == "random":
            style = random.choice(list(PROGRESS_ANIMATIONS.keys()))

        if style in PROGRESS_ANIMATIONS:
            return PROGRESS_ANIMATIONS[style]["frames"](percent)
        return "N/A"
