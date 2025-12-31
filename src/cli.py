"""CLI commands for fftpeg operations."""

import sys
from pathlib import Path
from typing import Optional

from .utils.downloader import VideoDownloader
from .utils.database import Database
from .utils.symlink_manager import SymlinkManager
from .config.settings import Config


class CLI:
    """Command-line interface for fftpeg operations."""

    def __init__(self):
        """Initialize CLI with necessary components."""
        self.config = Config()
        self.db = Database()

        org_paths = self.config.get_organization_paths()
        base_path = org_paths['base'].parent
        self.symlink_manager = SymlinkManager(base_path)
        self.downloader = VideoDownloader(self.config, self.db, self.symlink_manager)

    def pull(self, url: str, tags: Optional[str] = None, preview: bool = False) -> int:
        """Pull/download video from URL.

        Args:
            url: Video URL
            tags: Comma-separated tags
            preview: If True, only show info without downloading

        Returns:
            Exit code (0 for success)
        """
        print(f"📥 Pull: {url}")

        if preview:
            print("Fetching video info...")
            info = self.downloader.get_video_info(url)

            if info:
                duration_min = int(info['duration'] // 60) if info.get('duration') else 0
                duration_sec = int(info['duration'] % 60) if info.get('duration') else 0

                print(f"\n✓ Video Information:")
                print(f"  Title:    {info.get('title', 'Unknown')}")
                print(f"  Uploader: {info.get('uploader', 'Unknown')}")
                print(f"  Duration: {duration_min}:{duration_sec:02d}")
                print(f"  Views:    {info.get('view_count', 'Unknown'):,}" if info.get('view_count') else "  Views:    Unknown")
                return 0
            else:
                print("✗ Could not fetch video info", file=sys.stderr)
                return 1

        # Parse tags
        additional_tags = [t.strip() for t in tags.split(",")] if tags else []

        print("Downloading...")
        result = self.downloader.download(url, additional_tags=additional_tags)

        if result['status'] == 'success':
            print(f"\n✓ Download complete!")
            print(f"  File:   {result['filepath'].name}")
            print(f"  Source: {result['source']}")
            print(f"  Tags:   {', '.join(result['tags'])}")
            print(f"  Size:   {result['metadata']['size'] / (1024*1024):.1f} MB")
            print(f"\n  Organized in:")
            print(f"    • downloads/")
            print(f"    • by-source/{result['source']}/")
            for tag in result['tags']:
                print(f"    • by-tag/{tag}/")
            print(f"    • by-date/...")
            return 0

        elif result['status'] == 'exists':
            print(f"\nℹ  URL already downloaded:")
            print(f"  {result['file']['filepath']}")
            return 0

        elif result['status'] == 'duplicate':
            print(f"\nℹ  Duplicate file detected:")
            print(f"  {result['file']['filepath']}")
            return 0

        else:
            print(f"\n✗ Error: {result['message']}", file=sys.stderr)
            return 1

    def convert(self, input_file: str, output_file: str, codec: Optional[str] = None) -> int:
        """Convert video format.

        Args:
            input_file: Input video file
            output_file: Output video file
            codec: Video codec (default: copy)

        Returns:
            Exit code (0 for success)
        """
        import ffmpeg

        input_path = Path(input_file).expanduser().resolve()
        output_path = Path(output_file).expanduser().resolve()

        if not input_path.exists():
            print(f"✗ Error: Input file not found: {input_file}", file=sys.stderr)
            return 1

        print(f"🎬 Convert: {input_path.name} → {output_path.name}")

        try:
            stream = ffmpeg.input(str(input_path))

            if codec:
                stream = ffmpeg.output(stream, str(output_path), vcodec=codec)
            else:
                # Copy streams without re-encoding
                stream = ffmpeg.output(stream, str(output_path), codec='copy')

            # Show ffmpeg command
            cmd = ' '.join(ffmpeg.compile(stream))
            print(f"\n▶ Running: ffmpeg {cmd.split('ffmpeg')[1] if 'ffmpeg' in cmd else cmd}")

            ffmpeg.run(stream, overwrite_output=True)

            output_size = output_path.stat().st_size / (1024*1024)
            print(f"\n✓ Conversion complete!")
            print(f"  Output: {output_path}")
            print(f"  Size:   {output_size:.1f} MB")
            return 0

        except ffmpeg.Error as e:
            print(f"\n✗ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"\n✗ Error: {str(e)}", file=sys.stderr)
            return 1

    def compress(self, input_file: str, output_file: Optional[str] = None,
                 crf: int = 23, preset: str = "medium") -> int:
        """Compress video with quality settings.

        Args:
            input_file: Input video file
            output_file: Output file (default: input_compressed.ext)
            crf: CRF value (18-28, lower=better quality)
            preset: Encoding preset (ultrafast, fast, medium, slow, veryslow)

        Returns:
            Exit code (0 for success)
        """
        import ffmpeg

        input_path = Path(input_file).expanduser().resolve()

        if not input_path.exists():
            print(f"✗ Error: Input file not found: {input_file}", file=sys.stderr)
            return 1

        # Generate output filename if not provided
        if output_file is None:
            output_path = input_path.parent / f"{input_path.stem}_compressed{input_path.suffix}"
        else:
            output_path = Path(output_file).expanduser().resolve()

        print(f"🗜️  Compress: {input_path.name}")
        print(f"  CRF:    {crf} (lower=better quality)")
        print(f"  Preset: {preset}")

        try:
            stream = ffmpeg.input(str(input_path))
            stream = ffmpeg.output(
                stream,
                str(output_path),
                vcodec='libx264',
                crf=crf,
                preset=preset,
                acodec='aac'
            )

            # Show ffmpeg command
            cmd = ' '.join(ffmpeg.compile(stream))
            print(f"\n▶ Running: ffmpeg {cmd.split('ffmpeg')[1] if 'ffmpeg' in cmd else cmd}")

            ffmpeg.run(stream, overwrite_output=True)

            input_size = input_path.stat().st_size / (1024*1024)
            output_size = output_path.stat().st_size / (1024*1024)
            reduction = ((input_size - output_size) / input_size) * 100

            print(f"\n✓ Compression complete!")
            print(f"  Input:     {input_size:.1f} MB")
            print(f"  Output:    {output_size:.1f} MB")
            print(f"  Saved:     {reduction:.1f}%")
            print(f"  Location:  {output_path}")
            return 0

        except ffmpeg.Error as e:
            print(f"\n✗ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"\n✗ Error: {str(e)}", file=sys.stderr)
            return 1

    def extract_audio(self, input_file: str, output_file: Optional[str] = None,
                      format: str = "mp3", quality: str = "320k") -> int:
        """Extract audio from video.

        Args:
            input_file: Input video file
            output_file: Output audio file (default: input.mp3)
            format: Audio format (mp3, m4a, flac, wav)
            quality: Audio quality/bitrate (e.g., 320k, 192k)

        Returns:
            Exit code (0 for success)
        """
        import ffmpeg

        input_path = Path(input_file).expanduser().resolve()

        if not input_path.exists():
            print(f"✗ Error: Input file not found: {input_file}", file=sys.stderr)
            return 1

        # Generate output filename if not provided
        if output_file is None:
            output_path = input_path.parent / f"{input_path.stem}.{format}"
        else:
            output_path = Path(output_file).expanduser().resolve()

        print(f"🎵 Extract Audio: {input_path.name}")
        print(f"  Format:  {format}")
        print(f"  Quality: {quality}")

        try:
            stream = ffmpeg.input(str(input_path))

            # Map audio codec based on format
            codec_map = {
                'mp3': 'libmp3lame',
                'm4a': 'aac',
                'flac': 'flac',
                'wav': 'pcm_s16le'
            }

            acodec = codec_map.get(format, 'libmp3lame')

            stream = ffmpeg.output(
                stream,
                str(output_path),
                acodec=acodec,
                audio_bitrate=quality,
                vn=None  # No video
            )

            # Show ffmpeg command
            cmd = ' '.join(ffmpeg.compile(stream))
            print(f"\n▶ Running: ffmpeg {cmd.split('ffmpeg')[1] if 'ffmpeg' in cmd else cmd}")

            ffmpeg.run(stream, overwrite_output=True)

            output_size = output_path.stat().st_size / (1024*1024)
            print(f"\n✓ Audio extraction complete!")
            print(f"  Output: {output_path}")
            print(f"  Size:   {output_size:.1f} MB")
            return 0

        except ffmpeg.Error as e:
            print(f"\n✗ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"\n✗ Error: {str(e)}", file=sys.stderr)
            return 1

    def trim(self, input_file: str, output_file: Optional[str] = None,
             start: str = "00:00:00", end: Optional[str] = None,
             duration: Optional[str] = None) -> int:
        """Trim/cut video.

        Args:
            input_file: Input video file
            output_file: Output file (default: input_trimmed.ext)
            start: Start time (HH:MM:SS)
            end: End time (HH:MM:SS) - mutually exclusive with duration
            duration: Duration from start (HH:MM:SS) - mutually exclusive with end

        Returns:
            Exit code (0 for success)
        """
        import ffmpeg

        input_path = Path(input_file).expanduser().resolve()

        if not input_path.exists():
            print(f"✗ Error: Input file not found: {input_file}", file=sys.stderr)
            return 1

        if end and duration:
            print(f"✗ Error: Cannot specify both end and duration", file=sys.stderr)
            return 1

        # Generate output filename if not provided
        if output_file is None:
            output_path = input_path.parent / f"{input_path.stem}_trimmed{input_path.suffix}"
        else:
            output_path = Path(output_file).expanduser().resolve()

        print(f"✂️  Trim: {input_path.name}")
        print(f"  Start: {start}")
        if end:
            print(f"  End:   {end}")
        if duration:
            print(f"  Duration: {duration}")

        try:
            stream = ffmpeg.input(str(input_path), ss=start)

            if end:
                stream = ffmpeg.output(stream, str(output_path), to=end, codec='copy')
            elif duration:
                stream = ffmpeg.output(stream, str(output_path), t=duration, codec='copy')
            else:
                stream = ffmpeg.output(stream, str(output_path), codec='copy')

            # Show ffmpeg command
            cmd = ' '.join(ffmpeg.compile(stream))
            print(f"\n▶ Running: ffmpeg {cmd.split('ffmpeg')[1] if 'ffmpeg' in cmd else cmd}")

            ffmpeg.run(stream, overwrite_output=True)

            output_size = output_path.stat().st_size / (1024*1024)
            print(f"\n✓ Trim complete!")
            print(f"  Output: {output_path}")
            print(f"  Size:   {output_size:.1f} MB")
            return 0

        except ffmpeg.Error as e:
            print(f"\n✗ FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"\n✗ Error: {str(e)}", file=sys.stderr)
            return 1
