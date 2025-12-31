"""Configuration management for fftpeg."""

import json
from pathlib import Path
from typing import Dict, Any, Optional


DEFAULT_CONFIG = {
    "download_path": "~/Videos/fftpeg/downloads",
    "organize_by_source": True,
    "organize_by_tag": True,
    "organize_by_date": True,
    "source_formats": {
        "youtube": {
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "merge_output_format": "mp4"
        },
        "twitter": {
            "format": "best"
        },
        "instagram": {
            "format": "best[height<=720]"
        },
        "vimeo": {
            "format": "best"
        },
        "tiktok": {
            "format": "best"
        },
        "twitch": {
            "format": "best"
        },
        "reddit": {
            "format": "best"
        },
        "default": {
            "format": "best"
        }
    },
    "auto_tag_rules": [
        {"source": "youtube", "tag": "youtube", "enabled": True},
        {"source": "twitter", "tag": "twitter", "enabled": True},
        {"source": "instagram", "tag": "instagram", "enabled": True},
        {"source": "vimeo", "tag": "vimeo", "enabled": True},
        {"source": "tiktok", "tag": "tiktok", "enabled": True},
        {"source": "twitch", "tag": "twitch", "enabled": True},
        {"source": "reddit", "tag": "reddit", "enabled": True}
    ]
}


class Config:
    """Configuration manager for fftpeg."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration.

        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            config_dir = Path.home() / ".config" / "fftpeg"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "config.json"

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    config = DEFAULT_CONFIG.copy()
                    config.update(loaded)
                    return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Error loading config: {e}. Using defaults.")
                return DEFAULT_CONFIG.copy()
        else:
            # Create default config
            config = DEFAULT_CONFIG.copy()
            self.save()
            return config

    def save(self):
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., 'source_formats.youtube')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """Set a configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        config[keys[-1]] = value
        self.save()

    def get_download_path(self) -> Path:
        """Get the download path as a Path object.

        Returns:
            Expanded download path
        """
        path_str = self.get("download_path", "~/Videos/fftpeg/downloads")
        return Path(path_str).expanduser().resolve()

    def get_source_format(self, source: str) -> Dict[str, str]:
        """Get format configuration for a source.

        Args:
            source: Source platform name

        Returns:
            Format configuration dict
        """
        formats = self.get("source_formats", {})
        return formats.get(source, formats.get("default", {"format": "best"}))

    def get_organization_paths(self) -> Dict[str, Path]:
        """Get paths for organization structures.

        Returns:
            Dict with keys: base, by_source, by_tag, by_date
        """
        base = self.get_download_path()
        return {
            "base": base,
            "by_source": base.parent / "by-source",
            "by_tag": base.parent / "by-tag",
            "by_date": base.parent / "by-date"
        }

    def get_auto_tag_rules(self) -> list:
        """Get enabled auto-tag rules.

        Returns:
            List of rule dicts
        """
        rules = self.get("auto_tag_rules", [])
        return [r for r in rules if r.get("enabled", True)]

    def add_auto_tag_rule(self, source: str, tag: str):
        """Add a new auto-tag rule.

        Args:
            source: Source platform
            tag: Tag to auto-assign
        """
        rules = self.config.get("auto_tag_rules", [])

        # Check if rule already exists
        for rule in rules:
            if rule["source"] == source and rule["tag"] == tag:
                rule["enabled"] = True
                self.save()
                return

        # Add new rule
        rules.append({"source": source, "tag": tag, "enabled": True})
        self.config["auto_tag_rules"] = rules
        self.save()

    def remove_auto_tag_rule(self, source: str, tag: str):
        """Remove an auto-tag rule.

        Args:
            source: Source platform
            tag: Tag to remove
        """
        rules = self.config.get("auto_tag_rules", [])
        rules = [r for r in rules if not (r["source"] == source and r["tag"] == tag)]
        self.config["auto_tag_rules"] = rules
        self.save()
