"""Symlink manager for organizing files by tags, sources, and dates."""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict


class SymlinkManager:
    """Manages symlink-based file organization."""

    def __init__(self, base_path: Path):
        """Initialize symlink manager.

        Args:
            base_path: Base directory for organization (parent of downloads/)
        """
        self.base_path = base_path
        self.by_source_path = base_path / "by-source"
        self.by_tag_path = base_path / "by-tag"
        self.by_date_path = base_path / "by-date"

        # Create organization directories
        self.by_source_path.mkdir(parents=True, exist_ok=True)
        self.by_tag_path.mkdir(parents=True, exist_ok=True)
        self.by_date_path.mkdir(parents=True, exist_ok=True)

    def create_symlink(self, source: Path, link: Path) -> bool:
        """Create a symlink, handling existing links.

        Args:
            source: Path to actual file
            link: Path where symlink should be created

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directory if needed
            link.parent.mkdir(parents=True, exist_ok=True)

            # Remove existing symlink if it exists
            if link.is_symlink():
                link.unlink()
            elif link.exists():
                # Don't overwrite actual files
                print(f"Warning: {link} exists and is not a symlink")
                return False

            # Create relative symlink for portability
            relative_source = os.path.relpath(source, link.parent)
            link.symlink_to(relative_source)
            return True

        except (OSError, IOError) as e:
            print(f"Error creating symlink: {e}")
            return False

    def organize_by_source(self, filepath: Path, source: str) -> bool:
        """Create symlink in by-source directory.

        Args:
            filepath: Path to actual file
            source: Source platform (youtube, twitter, etc.)

        Returns:
            True if successful
        """
        source_dir = self.by_source_path / source
        link_path = source_dir / filepath.name
        return self.create_symlink(filepath, link_path)

    def organize_by_tag(self, filepath: Path, tag: str) -> bool:
        """Create symlink in by-tag directory.

        Args:
            filepath: Path to actual file
            tag: Tag name

        Returns:
            True if successful
        """
        tag_dir = self.by_tag_path / tag
        link_path = tag_dir / filepath.name
        return self.create_symlink(filepath, link_path)

    def organize_by_date(self, filepath: Path, date: Optional[datetime] = None) -> bool:
        """Create symlink in by-date directory.

        Args:
            filepath: Path to actual file
            date: Download date (uses current date if None)

        Returns:
            True if successful
        """
        if date is None:
            date = datetime.now()

        # Organize by YYYY-MM
        date_str = date.strftime("%Y-%m")
        date_dir = self.by_date_path / date_str
        link_path = date_dir / filepath.name
        return self.create_symlink(filepath, link_path)

    def organize_file(
        self,
        filepath: Path,
        source: str,
        tags: List[str],
        date: Optional[datetime] = None,
        organize_source: bool = True,
        organize_tags: bool = True,
        organize_date: bool = True
    ) -> Dict[str, bool]:
        """Organize a file with all applicable symlinks.

        Args:
            filepath: Path to actual file
            source: Source platform
            tags: List of tags
            date: Download date
            organize_source: Whether to create source symlink
            organize_tags: Whether to create tag symlinks
            organize_date: Whether to create date symlink

        Returns:
            Dict with results for each organization type
        """
        results = {}

        if organize_source:
            results['source'] = self.organize_by_source(filepath, source)

        if organize_tags:
            results['tags'] = {}
            for tag in tags:
                results['tags'][tag] = self.organize_by_tag(filepath, tag)

        if organize_date:
            results['date'] = self.organize_by_date(filepath, date)

        return results

    def remove_broken_symlinks(self, directory: Optional[Path] = None):
        """Remove broken symlinks from organization directories.

        Args:
            directory: Specific directory to clean (None = all)
        """
        directories = [directory] if directory else [
            self.by_source_path,
            self.by_tag_path,
            self.by_date_path
        ]

        for dir_path in directories:
            if not dir_path.exists():
                continue

            for item in dir_path.rglob("*"):
                if item.is_symlink() and not item.exists():
                    try:
                        item.unlink()
                        print(f"Removed broken symlink: {item}")
                    except OSError as e:
                        print(f"Error removing {item}: {e}")

    def get_organization_stats(self) -> Dict[str, Dict]:
        """Get statistics about organized files.

        Returns:
            Dict with stats for each organization type
        """
        stats = {}

        # Source stats
        if self.by_source_path.exists():
            sources = {}
            for source_dir in self.by_source_path.iterdir():
                if source_dir.is_dir():
                    count = sum(1 for _ in source_dir.iterdir() if _.is_symlink())
                    sources[source_dir.name] = count
            stats['by_source'] = sources

        # Tag stats
        if self.by_tag_path.exists():
            tags = {}
            for tag_dir in self.by_tag_path.iterdir():
                if tag_dir.is_dir():
                    count = sum(1 for _ in tag_dir.iterdir() if _.is_symlink())
                    tags[tag_dir.name] = count
            stats['by_tag'] = tags

        # Date stats
        if self.by_date_path.exists():
            dates = {}
            for date_dir in self.by_date_path.iterdir():
                if date_dir.is_dir():
                    count = sum(1 for _ in date_dir.iterdir() if _.is_symlink())
                    dates[date_dir.name] = count
            stats['by_date'] = dates

        return stats

    def list_files_by_source(self, source: str) -> List[Path]:
        """List all files from a specific source.

        Args:
            source: Source platform name

        Returns:
            List of file paths (resolved from symlinks)
        """
        source_dir = self.by_source_path / source
        if not source_dir.exists():
            return []

        files = []
        for link in source_dir.iterdir():
            if link.is_symlink() and link.exists():
                files.append(link.resolve())

        return files

    def list_files_by_tag(self, tag: str) -> List[Path]:
        """List all files with a specific tag.

        Args:
            tag: Tag name

        Returns:
            List of file paths (resolved from symlinks)
        """
        tag_dir = self.by_tag_path / tag
        if not tag_dir.exists():
            return []

        files = []
        for link in tag_dir.iterdir():
            if link.is_symlink() and link.exists():
                files.append(link.resolve())

        return files
