"""
YouTube Video Upload and Scheduler Script

This script iterates through all video files in a folder and uploads them
to your YouTube channel, scheduling each video to publish on consecutive days,
with multiple videos per day (configurable time slots).

After a successful upload, the video is moved to the "sent" folder.

Features:
- Automatic quota reset time checking (05:00 BRT)
- Immediate stop when daily quota exceeded error is detected
- Configurable via command-line arguments
- Relative paths based on script location
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

# Fix encoding for Windows console to support emojis
if sys.platform == 'win32':
    try:
        # Try to set UTF-8 encoding for stdout/stderr
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        # If reconfiguration fails, continue without it
        pass

# Platform-specific imports for file locking
if sys.platform != 'win32':
    import fcntl  # For file locking (Unix)

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import ResumableUploadError, HttpError
from tqdm import tqdm
import upload_tracker

# Required scopes for video uploads, captions, and thumbnails
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"  # For captions and thumbnails
]

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
CLIPS_FOLDER = SCRIPT_DIR / "clips"
SENT_FOLDER = SCRIPT_DIR / "sent"
CLIENT_SECRETS_FILE = SCRIPT_DIR / "client_secret.json"
TOKEN_FILE = SCRIPT_DIR / "token.json"
CONFIG_FILE = SCRIPT_DIR / "config.json"
LOGS_DIR = SCRIPT_DIR / "logs"
HISTORY_FILE = LOGS_DIR / "upload_history.json"
ERROR_LOG_FILE = LOGS_DIR / "error_log.txt"
LOCK_FILE = SCRIPT_DIR / ".script.lock"
BACKUP_DIR = SCRIPT_DIR / "backups"

# Create logs directory if it doesn't exist
LOGS_DIR.mkdir(exist_ok=True)


def load_config() -> dict[str, Any]:
    """Load configuration from config.json file, or return defaults if not found."""
    default_config = {
        "default_timezone": "America/Sao_Paulo",
        "default_hour_slots": [8, 18],
        "default_category_id": "20",
        "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
        "auto_retry_on_failure": False,
        "max_retries": 3,
        "privacy_status": "private",
        "description": "",
        "tags": []
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                # Merge user config with defaults (user config takes precedence)
                config = {**default_config, **user_config}
                return config
        except json.JSONDecodeError as e:
            print(f"⚠️  WARNING: Invalid JSON in {CONFIG_FILE.name}: {e}")
            print(f"Using default configuration. Please check README.md for configuration examples.\n")
            return default_config
        except Exception as e:
            print(f"⚠️  WARNING: Error reading {CONFIG_FILE.name}: {e}")
            print(f"Using default configuration.\n")
            return default_config
    else:
        return default_config


def parse_arguments(config: dict[str, Any]) -> argparse.Namespace:
    """Parse command-line arguments with defaults from config file."""
    parser = argparse.ArgumentParser(
        description="Upload and schedule videos to YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use all default values from config.json (or built-in defaults)
  python youtube_bulk_scheduler.py

  # Custom start date and timezone
  python youtube_bulk_scheduler.py --start-date 2025-12-01 --timezone America/New_York

  # Custom time slots (one video per day at 10am)
  python youtube_bulk_scheduler.py --hour-slots 10

  # Multiple custom time slots
  python youtube_bulk_scheduler.py --hour-slots 9 12 15 18

  # Custom category (Gaming category ID)
  python youtube_bulk_scheduler.py --category-id 20
        """
    )

    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="Start date for first video (YYYY-MM-DD). Defaults to today's date."
    )

    parser.add_argument(
        "--timezone",
        type=str,
        default=config.get("default_timezone", "America/Sao_Paulo"),
        help=f"Timezone for scheduling. Default from config: {config.get('default_timezone', 'America/Sao_Paulo')}"
    )

    parser.add_argument(
        "--hour-slots",
        type=int,
        nargs="+",
        default=config.get("default_hour_slots", [8, 18]),
        help=f"Hour slots per day (24-hour format). Default from config: {config.get('default_hour_slots', [8, 18])}"
    )

    parser.add_argument(
        "--category-id",
        type=str,
        default=config.get("default_category_id", "20"),
        help=f"YouTube category ID. Default from config: {config.get('default_category_id', '20')} (Gaming)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be done without actually uploading videos"
    )

    parser.add_argument(
        "--description",
        type=str,
        default=config.get("description", ""),
        help="Description for all videos. Default from config."
    )

    parser.add_argument(
        "--tags",
        type=str,
        default=None,
        help="Tags for all videos (comma-separated). Default from config."
    )
    
    parser.add_argument(
        "--platforms",
        type=str,
        nargs="+",
        default=["youtube"],
        help="Platforms to upload to. Used for tracking when uploading to multiple platforms. Default: youtube"
    )

    return parser.parse_args()


def parse_start_date(date_str: str | None, timezone: ZoneInfo) -> datetime:
    """Parse start date string or return today's date."""
    if date_str:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return datetime(
                date_obj.year, date_obj.month, date_obj.day,
                0, 0, 0, tzinfo=timezone
            )
        except ValueError as e:
            raise ValueError(
                f"Invalid date format '{date_str}'. Use YYYY-MM-DD format. Error: {e}"
            )
    else:
        # Default to today
        return datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}h {minutes}m {secs}s"


def sanitize_title(title: str) -> tuple[str, list[str]]:
    """
    Sanitize video title by removing invalid characters for YouTube.
    
    YouTube doesn't allow certain characters in titles. This function:
    - Removes invalid characters
    - Warns about length (max 100 characters)
    
    Returns:
        tuple: (sanitized_title, warnings_list)
    """
    warnings = []
    
    # YouTube title restrictions: no < > characters
    # Also remove other potentially problematic characters
    invalid_chars = ['<', '>']
    sanitized = title
    
    for char in invalid_chars:
        if char in sanitized:
            sanitized = sanitized.replace(char, '')
            warnings.append(f"Removed invalid character: '{char}'")
    
    # Check length (YouTube limit: 100 characters)
    if len(sanitized) > 100:
        warnings.append(f"Title is {len(sanitized)} characters (max 100). It will be truncated.")
        sanitized = sanitized[:100]
    elif len(sanitized) == 0:
        warnings.append("Title is empty after sanitization. Using default.")
        sanitized = "Untitled Video"
    
    return sanitized, warnings


def load_upload_history() -> list[dict[str, Any]]:
    """Load upload history from JSON file."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                if isinstance(history, list):
                    return history
                else:
                    # Legacy format or corrupted, return empty list
                    return []
        except (json.JSONDecodeError, Exception):
            return []
    return []


def save_upload_history(history: list[dict[str, Any]]) -> None:
    """Save upload history to JSON file."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  WARNING: Could not save upload history: {e}")


def add_upload_to_history(
    filename: str,
    youtube_id: str,
    scheduled_time: datetime,
    file_size: int,
    upload_time: float,
    upload_speed: float,
    status: str = "success",
    error_message: str = None
) -> None:
    """Add an upload entry to the history."""
    history = load_upload_history()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "filename": filename,
        "youtube_id": youtube_id,
        "scheduled_time": scheduled_time.isoformat(),
        "scheduled_time_readable": scheduled_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "file_size_bytes": file_size,
        "file_size_readable": format_file_size(file_size),
        "upload_time_seconds": upload_time,
        "upload_time_readable": format_duration(upload_time),
        "upload_speed_bytes_per_second": upload_speed,
        "upload_speed_readable": format_file_size(upload_speed) + "/s",
        "status": status,
        "error_message": error_message
    }
    
    history.append(entry)
    save_upload_history(history)


@contextmanager
def file_lock(lock_path: Path):
    """
    Context manager for file-based locking to prevent concurrent executions.
    Works on both Unix and Windows.
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = None
    try:
        # Try to create lock file exclusively
        try:
            if sys.platform == 'win32':
                # Windows: use msvcrt for locking
                import msvcrt
                lock_file = open(lock_path, 'w')
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                # Unix: use fcntl
                lock_file = open(lock_path, 'w')
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, OSError, PermissionError):
            if lock_file:
                lock_file.close()
            raise RuntimeError("Another instance of the script is already running. Please wait for it to finish.")
        
        # Write PID to lock file
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        
        yield
        
    finally:
        # Release lock and clean up
        if lock_file:
            try:
                if sys.platform == 'win32':
                    import msvcrt
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                lock_file.close()
            except:
                pass
        
        # Clean up lock file
        try:
            if lock_path.exists():
                lock_path.unlink()
        except:
            pass


def log_error(error_message: str, error_type: str = "ERROR", exception: Exception | None = None) -> None:
    """
    Log error to both console and error log file.
    
    Args:
        error_message: The error message to log
        error_type: Type of error (ERROR, WARNING, etc.)
        exception: Optional exception object for detailed logging
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {error_type}: {error_message}"
    
    if exception:
        import traceback
        log_entry += f"\nException details:\n{traceback.format_exc()}"
    
    # Print to console
    print(log_entry)
    
    # Append to log file
    try:
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n" + "=" * 80 + "\n")
    except Exception as e:
        # If we can't write to log file, at least print it
        print(f"⚠️  WARNING: Could not write to error log file: {e}")


def get_authenticated_service(client_secrets_path: Path, token_path: Path, show_status: bool = True):
    """Authenticate using OAuth with client_secret.json."""
    if show_status:
        print("🔐 Authenticating with YouTube API...")
    
    creds = None

    if token_path.exists():
        if show_status:
            print("   ✓ Loading saved credentials...")
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            if show_status:
                print("   ↻ Refreshing expired token...")
            try:
                creds.refresh(Request())
                if show_status:
                    print("   ✓ Token refreshed successfully")
            except Exception as e:
                # If refresh fails (e.g., invalid_scope), delete token and re-authenticate
                error_str = str(e)
                if 'invalid_scope' in error_str or 'Bad Request' in error_str:
                    if show_status:
                        print("   ⚠️  Token has invalid scopes. Deleting old token and re-authenticating...")
                    token_path.unlink(missing_ok=True)
                    creds = None  # Force re-authentication
                else:
                    raise  # Re-raise if it's a different error
        
        # If we still don't have valid credentials, do full authentication
        if not creds or not creds.valid:
            if not client_secrets_path.exists():
                raise FileNotFoundError(
                    f"\n❌ ERROR: {client_secrets_path.name} not found!\n"
                    f"\nThe script requires {client_secrets_path.name} for YouTube API authentication.\n"
                    f"\nTo fix this:\n"
                    f"1. Go to https://console.cloud.google.com/\n"
                    f"2. Create a project or select an existing one\n"
                    f"3. Enable YouTube Data API v3\n"
                    f"4. Create OAuth 2.0 credentials (Desktop application)\n"
                    f"5. Download the credentials and save as '{client_secrets_path.name}' in this directory\n"
                    f"6. See {client_secrets_path.name.replace('.json', '_sample.json')} for the expected format\n"
                )

            if show_status:
                print("   🌐 Opening browser for authentication...")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secrets_path), SCOPES
            )
            creds = flow.run_local_server(port=0)
            if show_status:
                print("   ✓ Authentication successful")

        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    if show_status:
        print("   ✓ Ready to upload videos\n")
    
    return build("youtube", "v3", credentials=creds)


def find_related_files(video_path: Path) -> dict[str, Path | None]:
    """
    Find related files (subtitles, thumbnails) for a video.
    
    Returns:
        dict with keys: 'subtitle', 'thumbnail'
    """
    base_name = video_path.stem
    video_dir = video_path.parent
    
    # Look for subtitle files (.srt, .vtt)
    subtitle = None
    for ext in ['.srt', '.vtt']:
        subtitle_path = video_dir / f"{base_name}{ext}"
        if subtitle_path.exists():
            subtitle = subtitle_path
            break
    
    # Look for thumbnail (.png)
    thumbnail = None
    thumbnail_path = video_dir / f"{base_name}.png"
    if thumbnail_path.exists():
        thumbnail = thumbnail_path
    
    return {
        'subtitle': subtitle,
        'thumbnail': thumbnail
    }


def upload_and_schedule(
    video_path: Path,
    publish_time: datetime,
    youtube,
    category_id: str,
    privacy_status: str = "private",
    video_number: int = 0,
    total_videos: int = 0,
    dry_run: bool = False,
    description: str = "",
    tags: list[str] | None = None
) -> dict:
    """Upload a video and schedule it for publication."""
    raw_title = video_path.stem
    title, title_warnings = sanitize_title(raw_title)
    
    # Show warnings if any
    if title_warnings:
        for warning in title_warnings:
            print(f"   ⚠️  Title warning for '{raw_title}': {warning}")
    
    # Use provided description, default to empty string
    if tags is None:
        tags = []
    
    file_size = video_path.stat().st_size
    start_time = time.time()
    
    # Find related files (subtitles, thumbnails)
    related_files = find_related_files(video_path)
    
    # If dry run, just return preview info
    if dry_run:
        return {
            'dry_run': True,
            'title': title,
            'raw_title': raw_title,
            'title_warnings': title_warnings,
            'file_size': file_size,
            'scheduled_time': publish_time,
            'has_subtitle': related_files['subtitle'] is not None,
            'has_thumbnail': related_files['thumbnail'] is not None
        }

    # Prepare video metadata
    snippet_data = {
        "title": title,
        "description": description,
        "categoryId": category_id,
    }
    
    # Add tags if provided (YouTube API requires tags to be a list)
    if tags:
        snippet_data["tags"] = tags
    
    body = {
        "snippet": snippet_data,
        "status": {
            "privacyStatus": privacy_status,
            "publishAt": publish_time.isoformat(),
        },
    }

    # Create media upload object
    media = MediaFileUpload(
        str(video_path),
        chunksize=-1,
        resumable=True
    )

    # Create upload request
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    # Upload with progress bar
    response = None
    last_uploaded = 0
    
    # Create progress bar
    progress_bar = tqdm(
        total=file_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
        desc=f"📤 [{video_number}/{total_videos}] {title[:40]:<40}",
        ncols=100,
        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
    )

    while response is None:
        try:
            status, response = request.next_chunk()
        except (ResumableUploadError, HttpError) as e:
            # Check if it's the upload limit exceeded error
            error_str = str(e)
            if 'uploadLimitExceeded' in error_str or 'exceeded the number of videos' in error_str:
                progress_bar.close()
                # Re-raise the error so it can be caught by the outer exception handler
                raise
            # For other errors, re-raise as well
            progress_bar.close()
            raise
        
        if status:
            uploaded_bytes = int(status.resumable_progress)
            # Update progress bar with the difference
            progress_bar.update(uploaded_bytes - last_uploaded)
            last_uploaded = uploaded_bytes
            
            # Calculate and display speed
            elapsed = time.time() - start_time
            if elapsed > 0 and uploaded_bytes > 0:
                speed = uploaded_bytes / elapsed
                remaining_bytes = file_size - uploaded_bytes
                eta_seconds = remaining_bytes / speed if speed > 0 else 0
                progress_bar.set_postfix({
                    'speed': format_file_size(speed) + '/s',
                    'eta': format_duration(eta_seconds)
                })

    # Ensure progress bar is at 100%
    if last_uploaded < file_size:
        progress_bar.update(file_size - last_uploaded)
    progress_bar.close()

    # Calculate upload statistics
    upload_time = time.time() - start_time
    upload_speed = file_size / upload_time if upload_time > 0 else 0
    youtube_id = response.get('id')

    # Upload subtitle if available
    subtitle_uploaded = False
    if related_files['subtitle']:
        try:
            subtitle_path = related_files['subtitle']
            # Determine language from filename (e.g., video.pt-BR.srt -> pt-BR)
            # Default to 'en' if no language code found
            lang_code = 'en'
            if '.' in subtitle_path.stem:
                parts = subtitle_path.stem.split('.')
                if len(parts) > 1:
                    potential_lang = parts[-1]
                    # Simple check for language code format (2-5 chars, may contain -)
                    if len(potential_lang) <= 5 and potential_lang.replace('-', '').isalpha():
                        lang_code = potential_lang
            
            with open(subtitle_path, 'rb') as subtitle_file:
                youtube.captions().insert(
                    part='snippet',
                    body={
                        'snippet': {
                            'videoId': youtube_id,
                            'language': lang_code,
                            'name': f'{lang_code} subtitles'
                        }
                    },
                    media_body=subtitle_file
                ).execute()
            subtitle_uploaded = True
            print(f"     📝 Subtitle uploaded ({lang_code})")
        except Exception as e:
            print(f"     ⚠️  Failed to upload subtitle: {e}")

    # Upload thumbnail if available
    thumbnail_uploaded = False
    if related_files['thumbnail']:
        try:
            thumbnail_path = related_files['thumbnail']
            youtube.thumbnails().set(
                videoId=youtube_id,
                media_body=MediaFileUpload(str(thumbnail_path))
            ).execute()
            thumbnail_uploaded = True
            print(f"     🖼️  Thumbnail uploaded")
        except Exception as e:
            print(f"     ⚠️  Failed to upload thumbnail: {e}")

    # Print success message with details
    print(
        f"   ✓ Uploaded: {title[:50]}\n"
        f"     📊 Size: {format_file_size(file_size)} | "
        f"⏱️  Time: {format_duration(upload_time)} | "
        f"🚀 Speed: {format_file_size(upload_speed)}/s\n"
        f"     🆔 YouTube ID: {youtube_id}\n"
        f"     📅 Scheduled: {publish_time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
    )

    # Save to history
    add_upload_to_history(
        filename=video_path.name,
        youtube_id=youtube_id,
        scheduled_time=publish_time,
        file_size=file_size,
        upload_time=upload_time,
        upload_speed=upload_speed,
        status="success"
    )
    
    # Mark as uploaded in tracking system
    upload_tracker.mark_uploaded(
        filename=video_path.name,
        platform="youtube",
        video_id=youtube_id,
        scheduled_time=publish_time
    )

    return {
        'response': response,
        'upload_time': upload_time,
        'file_size': file_size,
        'upload_speed': upload_speed,
        'youtube_id': youtube_id,
        'subtitle_uploaded': subtitle_uploaded,
        'thumbnail_uploaded': thumbnail_uploaded
    }


def backup_files() -> None:
    """Create backup of important files (config, history) by appending to single files."""
    try:
        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().isoformat()
        
        # Backup config - append to single file
        if CONFIG_FILE.exists():
            backup_path = BACKUP_DIR / "config_backup.json"
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Create backup entry with timestamp
                backup_entry = {
                    'timestamp': timestamp,
                    'data': config_data
                }
                
                # Append as JSON line
                with open(backup_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(backup_entry, ensure_ascii=False) + '\n')
            except Exception as e:
                log_error(f"Failed to backup config: {e}", "WARNING", e)
        
        # Backup history - append to single file
        if HISTORY_FILE.exists():
            backup_path = BACKUP_DIR / "history_backup.json"
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                # Create backup entry with timestamp
                backup_entry = {
                    'timestamp': timestamp,
                    'data': history_data
                }
                
                # Append as JSON line
                with open(backup_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(backup_entry, ensure_ascii=False) + '\n')
            except Exception as e:
                log_error(f"Failed to backup history: {e}", "WARNING", e)
    except Exception as e:
        log_error(f"Failed to create backup: {e}", "WARNING", e)


def main() -> None:
    """Main function to orchestrate video uploads."""
    # Prevent concurrent executions
    try:
        with file_lock(LOCK_FILE):
            _main_impl()
    except RuntimeError as e:
        print(f"\n❌ {e}\n")
        sys.exit(1)


def _main_impl() -> None:
    """Internal main implementation (called within lock)."""
    # Load configuration
    config = load_config()
    args = parse_arguments(config)
    
    # Set default platforms if not specified
    if not hasattr(args, 'platforms'):
        args.platforms = ['youtube']
    
    # Create backup
    backup_files()

    # Validate and parse timezone
    try:
        timezone = ZoneInfo(args.timezone)
    except Exception as e:
        error_msg = f"Invalid timezone '{args.timezone}'\nCommon timezones: America/Sao_Paulo, America/New_York, Europe/London, Asia/Tokyo\nSee: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
        log_error(error_msg, "ERROR", e)
        sys.exit(1)

    # Validate and parse start date
    try:
        start_date = parse_start_date(args.start_date, timezone)
    except ValueError as e:
        log_error(str(e), "ERROR", e)
        sys.exit(1)

    # Validate hour slots
    if not args.hour_slots:
        log_error("At least one hour slot must be specified", "ERROR")
        sys.exit(1)

    for hour in args.hour_slots:
        if not (0 <= hour < 24):
            log_error(f"Invalid hour slot '{hour}'. Must be between 0 and 23.", "ERROR")
            sys.exit(1)

    # Process tags: convert from string to list if needed
    tags_list = []
    if args.tags:
        # If tags is a string (from CLI), split by comma
        if isinstance(args.tags, str):
            tags_list = [tag.strip() for tag in args.tags.split(',') if tag.strip()]
        elif isinstance(args.tags, list):
            tags_list = args.tags
    elif config.get("tags"):
        # Fall back to config if no CLI argument
        if isinstance(config["tags"], str):
            tags_list = [tag.strip() for tag in config["tags"].split(',') if tag.strip()]
        elif isinstance(config["tags"], list):
            tags_list = config["tags"]
    
    # Get description from args or config
    description = args.description if args.description else config.get("description", "")

    if args.dry_run:
        print("🔍 DRY-RUN MODE: Preview only, no videos will be uploaded\n")
    else:
        print("🚀 Starting uploads...\n")

    # Validate clips folder exists
    if not CLIPS_FOLDER.exists():
        error_msg = (
            f"Clips folder not found: {CLIPS_FOLDER}\n"
            f"\nPlease create a 'clips' folder in the same directory as this script:\n"
            f"{SCRIPT_DIR}\n"
            f"\nPlace your video files in the 'clips' folder."
        )
        log_error(error_msg, "ERROR")
        raise FileNotFoundError(error_msg)

    # Find video files (only those not yet uploaded to YouTube)
    print("📁 Scanning for video files...")
    video_extensions = set(config.get("video_extensions", [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"]))
    
    # Get platforms to check - default to YouTube only, but can be configured
    platforms_to_check = getattr(args, 'platforms', ['youtube'])
    
    # Get pending videos (not uploaded to YouTube yet)
    videos = upload_tracker.get_pending_videos(CLIPS_FOLDER, platforms_to_check, video_extensions)
    
    if not videos:
        print(f"   ✓ No pending videos found in: {CLIPS_FOLDER}")
        print(f"   (All videos have already been uploaded to YouTube)")
        return

    # Calculate total size
    total_size = sum(v.stat().st_size for v in videos)
    print(f"   ✓ Found {len(videos)} pending video(s) ({format_file_size(total_size)} total)\n")

    # Authenticate (skip in dry-run mode)
    youtube = None
    if not args.dry_run:
        try:
            youtube = get_authenticated_service(CLIENT_SECRETS_FILE, TOKEN_FILE, show_status=True)
        except FileNotFoundError as e:
            log_error(str(e), "ERROR", e)
            sys.exit(1)
        except Exception as e:
            log_error(f"Authentication failed: {e}", "ERROR", e)
            sys.exit(1)

    # Create sent folder
    SENT_FOLDER.mkdir(exist_ok=True)

    # Handle scheduling mode (daily or weekly)
    schedule_mode = config.get("schedule_mode", "daily")
    playlist_id = config.get("playlist_id", None)
    create_playlist = config.get("create_playlist", False)
    playlist_title = config.get("playlist_title", "Uploaded Videos")
    
    # Calculate base day based on schedule mode
    if schedule_mode == "weekly":
        schedule_day = config.get("schedule_day", "monday").lower()
        schedule_hour = config.get("schedule_hour", 10)
        
        # Map day names to weekday numbers (Monday = 0)
        day_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        target_weekday = day_map.get(schedule_day, 0)
        
        # Find next occurrence of target weekday
        current_date = start_date.date()
        days_ahead = target_weekday - current_date.weekday()
        if days_ahead < 0:  # Target day already passed this week
            days_ahead += 7
        base_day = current_date + timedelta(days=days_ahead)
        base_hour = schedule_hour
    else:
        # Daily mode (default)
        base_day = start_date.date()
        base_hour = None  # Will use hour_slots
    
    total_videos = len(videos)
    successful_uploads = 0
    failed_uploads = 0
    total_upload_time = 0
    total_uploaded_size = 0
    uploaded_video_ids = []  # For playlist management

    if args.dry_run:
        print("=" * 80)
        print(f"🔍 DRY-RUN: Preview of {total_videos} video(s) that would be processed")
        print("=" * 80 + "\n")
    else:
        print("=" * 80)
        print(f"🚀 Starting upload process: {total_videos} video(s) to process")
        print("=" * 80 + "\n")

    # Process videos
    for idx, video_path in enumerate(videos, start=1):
        if schedule_mode == "weekly":
            # Weekly mode: all videos on the same day/time, or spread across weeks
            week_offset = (idx - 1)  # Each video on a different week
            publish_dt = datetime(
                base_day.year,
                base_day.month,
                base_day.day,
                base_hour,
                0,
                0,
                tzinfo=timezone
            ) + timedelta(weeks=week_offset)
        else:
            # Daily mode (default): spread across days using hour slots
            day_offset = (idx - 1) // len(args.hour_slots)
            slot_index = (idx - 1) % len(args.hour_slots)
            publish_dt = datetime(
                base_day.year,
                base_day.month,
                base_day.day,
                args.hour_slots[slot_index],
                0,
                0,
                tzinfo=timezone
            ) + timedelta(days=day_offset)

        try:
            privacy_status = config.get("privacy_status", "private")
            result = upload_and_schedule(
                video_path,
                publish_dt,
                youtube,
                args.category_id,
                privacy_status,
                video_number=idx,
                total_videos=total_videos,
                dry_run=args.dry_run,
                description=description,
                tags=tags_list
            )
            
            # Handle dry-run results
            if args.dry_run:
                print(f"   📋 [{idx}/{total_videos}] {result['title'][:50]}")
                if result.get('title_warnings'):
                    for warning in result['title_warnings']:
                        print(f"      ⚠️  {warning}")
                print(f"      📅 Would be scheduled: {publish_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                print(f"      📊 Size: {format_file_size(result['file_size'])}\n")
                successful_uploads += 1
                continue

            # Track statistics
            successful_uploads += 1
            total_upload_time += result['upload_time']
            total_uploaded_size += result['file_size']
            
            # Collect video IDs for playlist
            if result.get('youtube_id'):
                uploaded_video_ids.append(result['youtube_id'])

            # Check if should move to sent (only if uploaded to all requested platforms)
            platforms_requested = getattr(args, 'platforms', ['youtube'])
            if upload_tracker.should_move_to_sent(video_path.name, platforms_requested):
                upload_tracker.move_to_sent(video_path)

        except (ResumableUploadError, HttpError) as e:
            # Check if it's the upload limit exceeded error
            error_str = str(e)
            if 'uploadLimitExceeded' in error_str or 'exceeded the number of videos' in error_str:
                print(f"\n❌ Upload limit exceeded. Stopping execution.")
                print(f"   The user has exceeded the number of videos they may upload.")
                log_error(
                    f"Upload limit exceeded. Stopping execution.",
                    "ERROR",
                    e
                )
                # Stop execution immediately
                break
            
            # For other HTTP/ResumableUpload errors, continue with normal error handling
            failed_uploads += 1
            error_msg = str(e)
            log_error(
                f"Error processing {video_path.name}: {error_msg}",
                "ERROR",
                e
            )
        except Exception as e:
            failed_uploads += 1
            error_msg = str(e)
            
            # Log error to console and file
            log_error(
                f"Error processing {video_path.name}: {error_msg}",
                "ERROR",
                e
            )

            # Mark as failed in tracking
            upload_tracker.mark_uploaded(
                filename=video_path.name,
                platform="youtube",
                error=error_msg
            )
            
            # Save failed upload to history
            try:
                file_size = video_path.stat().st_size if video_path.exists() else 0
            except:
                file_size = 0
                
            add_upload_to_history(
                filename=video_path.name,
                youtube_id=None,
                scheduled_time=publish_dt,
                file_size=file_size,
                upload_time=0,
                upload_speed=0,
                status="failed",
                error_message=error_msg
            )

            # Continue processing other videos even if one fails
            continue

    # Handle playlist management (after all uploads)
    if not args.dry_run and youtube and uploaded_video_ids:
        if playlist_id or create_playlist:
            try:
                if create_playlist:
                    # Create new playlist
                    playlist_response = youtube.playlists().insert(
                        part='snippet,status',
                        body={
                            'snippet': {
                                'title': playlist_title,
                                'description': f'Videos uploaded on {datetime.now().strftime("%Y-%m-%d")}'
                            },
                            'status': {
                                'privacyStatus': privacy_status
                            }
                        }
                    ).execute()
                    playlist_id = playlist_response['id']
                    print(f"\n📋 Created playlist: {playlist_title} (ID: {playlist_id})")
                
                # Add all uploaded videos to playlist
                if playlist_id:
                    for video_id in uploaded_video_ids:
                        youtube.playlistItems().insert(
                            part='snippet',
                            body={
                                'snippet': {
                                    'playlistId': playlist_id,
                                    'resourceId': {
                                        'kind': 'youtube#video',
                                        'videoId': video_id
                                    }
                                }
                            }
                        ).execute()
                    print(f"📋 Added {len(uploaded_video_ids)} video(s) to playlist")
            except Exception as e:
                log_error(f"Failed to manage playlist: {e}", "ERROR", e)

    # Print final summary
    print("=" * 80)
    print("📊 UPLOAD SUMMARY")
    print("=" * 80)
    print(f"   ✓ Successful: {successful_uploads}/{total_videos}")
    if failed_uploads > 0:
        print(f"   ❌ Failed: {failed_uploads}")
    if successful_uploads > 0:
        avg_speed = total_uploaded_size / total_upload_time if total_upload_time > 0 else 0
        print(f"   📦 Total uploaded: {format_file_size(total_uploaded_size)}")
        print(f"   ⏱️  Total time: {format_duration(total_upload_time)}")
        print(f"   🚀 Average speed: {format_file_size(avg_speed)}/s")
    print("=" * 80)
    
    # Save execution summary to history
    execution_summary = {
        "execution_timestamp": datetime.now().isoformat(),
        "execution_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_videos": total_videos,
        "successful_uploads": successful_uploads,
        "failed_uploads": failed_uploads,
        "total_uploaded_size_bytes": total_uploaded_size,
        "total_uploaded_size_readable": format_file_size(total_uploaded_size),
        "total_upload_time_seconds": total_upload_time,
        "total_upload_time_readable": format_duration(total_upload_time),
        "average_speed_bytes_per_second": total_uploaded_size / total_upload_time if total_upload_time > 0 else 0,
        "average_speed_readable": format_file_size(total_uploaded_size / total_upload_time) + "/s" if total_upload_time > 0 else "0 B/s"
    }
    
    # Load history and add summary
    history = load_upload_history()
    if not history or not isinstance(history[-1], dict) or "execution_timestamp" not in history[-1]:
        # Add summary as a separate entry
        history.append({"type": "execution_summary", **execution_summary})
    else:
        # Update last summary or add new one
        history.append({"type": "execution_summary", **execution_summary})
    
    if not args.dry_run:
        save_upload_history(history)
        print(f"\n💾 Upload history saved to: {HISTORY_FILE.name}")


if __name__ == "__main__":
    main()
