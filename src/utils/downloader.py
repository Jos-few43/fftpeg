"""Video downloader using yt-dlp."""

import hashlib
from pathlib import Path
from typing import Dict, Optional, Callable
from datetime import datetime
import yt_dlp

from .database import Database
from .symlink_manager import SymlinkManager
from ..config.settings import Config


class VideoDownloader:
    """Downloads videos using yt-dlp with smart organization."""

    def __init__(self, config: Config, db: Database, symlink_manager: SymlinkManager):
        """Initialize downloader.

        Args:
            config: Configuration manager
            db: Database instance
            symlink_manager: Symlink manager instance
        """
        self.config = config
        self.db = db
        self.symlink_manager = symlink_manager

    def _calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of a file.

        Args:
            filepath: Path to file

        Returns:
            Hex digest of file hash
        """
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _detect_source(self, url: str) -> str:
        """Detect source platform from URL.

        Args:
            url: Video URL

        Returns:
            Source platform name
        """
        url_lower = url.lower()

        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'vimeo.com' in url_lower:
            return 'vimeo'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'twitch.tv' in url_lower:
            return 'twitch'
        elif 'reddit.com' in url_lower or 'redd.it' in url_lower:
            return 'reddit'
        else:
            return 'unknown'

    def _get_auto_tags(self, source: str) -> list:
        """Get auto-tags for a source based on rules.

        Args:
            source: Source platform

        Returns:
            List of tag names
        """
        rules = self.config.get_auto_tag_rules()
        tags = []

        for rule in rules:
            if rule['source'] == source:
                tags.append(rule['tag'])

        return tags

    def download(
        self,
        url: str,
        progress_callback: Optional[Callable] = None,
        additional_tags: Optional[list] = None,
        custom_name: Optional[str] = None
    ) -> Dict:
        """Download a video from URL.

        Args:
            url: Video URL
            progress_callback: Optional callback for progress updates
            additional_tags: Additional tags to apply
            custom_name: Optional custom filename (without extension)

        Returns:
            Dict with download info and status
        """
        # Check if already downloaded
        existing = self.db.check_url_exists(url)
        if existing:
            return {
                'status': 'exists',
                'message': 'URL already downloaded',
                'file': existing
            }

        # Detect source
        source = self._detect_source(url)

        # Get format settings for source
        format_config = self.config.get_source_format(source)

        # Prepare download directory
        download_path = self.config.get_download_path()
        download_path.mkdir(parents=True, exist_ok=True)

        # Configure yt-dlp options
        # Use custom name if provided, otherwise use video title
        if custom_name:
            output_template = str(download_path / f'{custom_name}.%(ext)s')
        else:
            output_template = str(download_path / '%(title)s.%(ext)s')

        ydl_opts = {
            'format': format_config.get('format', 'best'),
            'outtmpl': output_template,
            'quiet': False,
            'no_warnings': False,
        }

        # Add merge output format if specified
        if 'merge_output_format' in format_config:
            ydl_opts['merge_output_format'] = format_config['merge_output_format']

        # Progress hook
        def progress_hook(d):
            if progress_callback and d['status'] == 'downloading':
                progress_callback(d)

        ydl_opts['progress_hooks'] = [progress_hook]

        try:
            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                # Get the actual downloaded file path
                if 'requested_downloads' in info:
                    filepath = Path(info['requested_downloads'][0]['filepath'])
                else:
                    # Fallback: construct from template
                    filename = ydl.prepare_filename(info)
                    filepath = Path(filename)

            # Calculate file hash
            file_hash = self._calculate_file_hash(filepath)

            # Check for duplicates by hash
            duplicate = self.db.check_hash_exists(file_hash)
            if duplicate:
                # File is duplicate, remove newly downloaded one
                filepath.unlink()
                return {
                    'status': 'duplicate',
                    'message': 'File already exists (duplicate hash)',
                    'file': duplicate
                }

            # Prepare metadata
            metadata = {
                'hash': file_hash,
                'size': filepath.stat().st_size,
                'duration': info.get('duration'),
                'codec': info.get('vcodec'),
                'resolution': f"{info.get('width')}x{info.get('height')}" if info.get('width') else None,
                'title': info.get('title'),
                'description': info.get('description'),
                'thumbnail': info.get('thumbnail'),
                'uploader': info.get('uploader')
            }

            # Add to database
            file_id = self.db.add_download(url, source, filepath, metadata)

            # Get auto-tags and add additional tags
            tags = self._get_auto_tags(source)
            if additional_tags:
                tags.extend(additional_tags)

            # Add tags to database
            for tag in tags:
                auto = tag in self._get_auto_tags(source)
                self.db.add_file_tag(file_id, tag, auto_assigned=auto)

            # Create symlinks for organization
            self.symlink_manager.organize_file(
                filepath=filepath,
                source=source,
                tags=tags,
                date=datetime.now(),
                organize_source=self.config.get('organize_by_source', True),
                organize_tags=self.config.get('organize_by_tag', True),
                organize_date=self.config.get('organize_by_date', True)
            )

            return {
                'status': 'success',
                'message': 'Download complete',
                'file_id': file_id,
                'filepath': filepath,
                'source': source,
                'tags': tags,
                'metadata': metadata
            }

        except yt_dlp.utils.DownloadError as e:
            return {
                'status': 'error',
                'message': f'Download error: {str(e)}'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            }

    def get_video_info(self, url: str) -> Optional[Dict]:
        """Get video information without downloading.

        Args:
            url: Video URL

        Returns:
            Video info dict or None if error
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'thumbnail': info.get('thumbnail'),
                    'description': info.get('description'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None
