"""Database utilities for managing downloads, tags, and metadata."""

import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager


class Database:
    """SQLite database manager for fftpeg."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        if db_path is None:
            config_dir = Path.home() / ".config" / "fftpeg"
            config_dir.mkdir(parents=True, exist_ok=True)
            db_path = config_dir / "fftpeg.db"

        self.db_path = db_path
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Downloads table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE,
                    source TEXT,
                    filepath TEXT UNIQUE,
                    filename TEXT,
                    hash TEXT,
                    size INTEGER,
                    duration REAL,
                    codec TEXT,
                    resolution TEXT,
                    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    title TEXT,
                    description TEXT,
                    thumbnail_url TEXT,
                    uploader TEXT
                )
            """)

            # Tags table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            """)

            # File-Tag relationship
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_tags (
                    file_id INTEGER,
                    tag_id INTEGER,
                    auto_assigned BOOLEAN DEFAULT 0,
                    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES downloads(id) ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
                    PRIMARY KEY (file_id, tag_id)
                )
            """)

            # Auto-tag rules
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auto_tag_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    UNIQUE(source, tag)
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloads_source ON downloads(source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_downloads_hash ON downloads(hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_tags_file ON file_tags(file_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_tags_tag ON file_tags(tag_id)")

            conn.commit()

    def add_download(
        self,
        url: str,
        source: str,
        filepath: Path,
        metadata: Dict
    ) -> int:
        """Add a download record to the database.

        Args:
            url: Source URL
            source: Source platform (youtube, twitter, etc.)
            filepath: Path to downloaded file
            metadata: Additional metadata dict

        Returns:
            ID of inserted record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO downloads (
                    url, source, filepath, filename, hash, size,
                    duration, codec, resolution, title, description,
                    thumbnail_url, uploader
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                url,
                source,
                str(filepath),
                filepath.name,
                metadata.get('hash'),
                metadata.get('size'),
                metadata.get('duration'),
                metadata.get('codec'),
                metadata.get('resolution'),
                metadata.get('title'),
                metadata.get('description'),
                metadata.get('thumbnail'),
                metadata.get('uploader')
            ))
            conn.commit()
            return cursor.lastrowid

    def get_or_create_tag(self, tag_name: str) -> int:
        """Get existing tag ID or create new tag.

        Args:
            tag_name: Name of the tag

        Returns:
            Tag ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Try to get existing
            cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
            result = cursor.fetchone()

            if result:
                return result[0]

            # Create new
            cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
            conn.commit()
            return cursor.lastrowid

    def add_file_tag(self, file_id: int, tag_name: str, auto_assigned: bool = False):
        """Add a tag to a file.

        Args:
            file_id: File ID from downloads table
            tag_name: Name of the tag
            auto_assigned: Whether this was auto-assigned by a rule
        """
        tag_id = self.get_or_create_tag(tag_name)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO file_tags (file_id, tag_id, auto_assigned)
                VALUES (?, ?, ?)
            """, (file_id, tag_id, auto_assigned))
            conn.commit()

    def get_file_tags(self, file_id: int) -> List[str]:
        """Get all tags for a file.

        Args:
            file_id: File ID from downloads table

        Returns:
            List of tag names
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.name FROM tags t
                JOIN file_tags ft ON t.id = ft.tag_id
                WHERE ft.file_id = ?
            """, (file_id,))
            return [row[0] for row in cursor.fetchall()]

    def get_auto_tag_rules(self) -> List[Dict]:
        """Get all enabled auto-tag rules.

        Returns:
            List of rule dicts with source and tag
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT source, tag FROM auto_tag_rules
                WHERE enabled = 1
            """)
            return [{"source": row[0], "tag": row[1]} for row in cursor.fetchall()]

    def add_auto_tag_rule(self, source: str, tag: str):
        """Add an auto-tag rule.

        Args:
            source: Source platform
            tag: Tag to auto-assign
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO auto_tag_rules (source, tag, enabled)
                VALUES (?, ?, 1)
            """, (source, tag))
            conn.commit()

    def check_url_exists(self, url: str) -> Optional[Dict]:
        """Check if URL has already been downloaded.

        Args:
            url: URL to check

        Returns:
            Download record dict if exists, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM downloads WHERE url = ?", (url,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def check_hash_exists(self, file_hash: str) -> Optional[Dict]:
        """Check if file with this hash already exists (duplicate detection).

        Args:
            file_hash: SHA256 hash of file

        Returns:
            Download record dict if exists, None otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM downloads WHERE hash = ?", (file_hash,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_files_by_tag(self, tag_name: str) -> List[Dict]:
        """Get all files with a specific tag.

        Args:
            tag_name: Tag to search for

        Returns:
            List of download records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT d.* FROM downloads d
                JOIN file_tags ft ON d.id = ft.file_id
                JOIN tags t ON ft.tag_id = t.id
                WHERE t.name = ?
            """, (tag_name,))
            return [dict(row) for row in cursor.fetchall()]

    def get_files_by_source(self, source: str) -> List[Dict]:
        """Get all files from a specific source.

        Args:
            source: Source platform

        Returns:
            List of download records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM downloads WHERE source = ?", (source,))
            return [dict(row) for row in cursor.fetchall()]

    def get_all_tags(self) -> List[str]:
        """Get all unique tags.

        Returns:
            List of tag names
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM tags ORDER BY name")
            return [row[0] for row in cursor.fetchall()]

    def get_all_sources(self) -> List[str]:
        """Get all unique sources.

        Returns:
            List of source names
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT source FROM downloads ORDER BY source")
            return [row[0] for row in cursor.fetchall()]
