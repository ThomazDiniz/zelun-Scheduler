# 📖 API Documentation

Technical documentation for the YouTube Bulk Scheduler script.

## Module Overview

The script is organized into several functional modules:

- **Configuration Management**: Loading and parsing configuration files
- **Authentication**: OAuth 2.0 authentication with YouTube API
- **Video Processing**: Upload, scheduling, and metadata management
- **File Management**: Handling videos, subtitles, thumbnails
- **History & Logging**: Tracking uploads and errors
- **Utilities**: Helper functions for formatting and validation

## Constants

### File Paths
```python
SCRIPT_DIR: Path              # Script directory
CLIPS_FOLDER: Path            # Input videos folder
SENT_FOLDER: Path             # Uploaded videos folder
CLIENT_SECRETS_FILE: Path     # OAuth credentials
TOKEN_FILE: Path              # OAuth token cache
CONFIG_FILE: Path             # Configuration file
HISTORY_FILE: Path            # Upload history
ERROR_LOG_FILE: Path          # Error log
LOCK_FILE: Path               # Lock file for concurrency
BACKUP_DIR: Path              # Backup directory
```

### API Scopes
```python
SCOPES: list[str] = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]
```

## Core Functions

### `load_config() -> dict`
Loads configuration from `config.json` or returns defaults.

**Returns**: Dictionary with configuration values

**Default Config**:
```python
{
    "default_timezone": "America/Sao_Paulo",
    "default_hour_slots": [8, 18],
    "default_category_id": "20",
    "video_extensions": [".mp4", ".mov", ".avi", ...],
    "privacy_status": "private"
}
```

### `parse_arguments(config: dict) -> argparse.Namespace`
Parses command-line arguments with defaults from config.

**Parameters**:
- `config`: Configuration dictionary

**Returns**: Parsed arguments object

**Arguments**:
- `--start-date`: Start date (YYYY-MM-DD)
- `--timezone`: Timezone string
- `--hour-slots`: List of hour slots (0-23)
- `--category-id`: YouTube category ID
- `--dry-run`: Preview mode flag

### `sanitize_title(title: str) -> tuple[str, list[str]]`
Sanitizes video title by removing invalid characters.

**Parameters**:
- `title`: Raw title string

**Returns**: Tuple of (sanitized_title, warnings_list)

**Behavior**:
- Removes invalid characters (`<`, `>`)
- Truncates if over 100 characters
- Returns warnings for any issues

### `format_file_size(size_bytes: int) -> str`
Formats file size in human-readable format.

**Example**: `524288000` → `"500.00 MB"`

### `format_duration(seconds: float) -> str`
Formats duration in human-readable format.

**Example**: `3661.5` → `"1h 1m 1s"`

### `find_related_files(video_path: Path) -> dict[str, Path | None]`
Finds related files (subtitles, thumbnails) for a video.

**Parameters**:
- `video_path`: Path to video file

**Returns**: Dictionary with keys:
- `'subtitle'`: Path to `.srt` or `.vtt` file (if exists)
- `'thumbnail'`: Path to `.png` file (if exists)

**File Naming**:
- Subtitle: `{video_name}.srt` or `{video_name}.vtt`
- Thumbnail: `{video_name}.png`
- Language codes: `{video_name}.{lang}.srt` (e.g., `video.pt-BR.srt`)

### `get_authenticated_service(client_secrets_path: Path, token_path: Path, show_status: bool = True) -> Any`
Authenticates with YouTube API using OAuth 2.0.

**Parameters**:
- `client_secrets_path`: Path to OAuth credentials
- `token_path`: Path to token cache file
- `show_status`: Whether to print status messages

**Returns**: YouTube API service object

**Behavior**:
- Loads cached token if available
- Refreshes expired tokens
- Opens browser for first-time authentication
- Saves token for future use

### `upload_and_schedule(...) -> dict[str, Any]`
Uploads a video and schedules it for publication.

**Parameters**:
- `video_path: Path` - Path to video file
- `publish_time: datetime` - Scheduled publication time
- `youtube: Any` - YouTube API service object
- `category_id: str` - YouTube category ID
- `privacy_status: str` - Privacy status ("private", "unlisted", "public")
- `video_number: int` - Current video number (for progress)
- `total_videos: int` - Total number of videos
- `dry_run: bool` - Preview mode flag

**Returns**: Dictionary with upload results:
```python
{
    'response': dict,           # YouTube API response
    'upload_time': float,      # Upload duration in seconds
    'file_size': int,          # File size in bytes
    'upload_speed': float,     # Upload speed in bytes/second
    'youtube_id': str,         # YouTube video ID
    'subtitle_uploaded': bool, # Whether subtitle was uploaded
    'thumbnail_uploaded': bool # Whether thumbnail was uploaded
}
```

**Behavior**:
- Sanitizes title
- Shows progress bar during upload
- Uploads subtitle if available
- Uploads thumbnail if available
- Returns preview info in dry-run mode

### `file_lock(lock_path: Path) -> contextmanager`
Context manager for file-based locking to prevent concurrent executions.

**Usage**:
```python
with file_lock(LOCK_FILE):
    # Code that should not run concurrently
    pass
```

**Platform Support**:
- Unix: Uses `fcntl`
- Windows: Uses `msvcrt`

### `log_error(error_message: str, error_type: str = "ERROR", exception: Exception | None = None) -> None`
Logs error to both console and error log file.

**Parameters**:
- `error_message`: Error message string
- `error_type`: Type of error ("ERROR", "WARNING", etc.)
- `exception`: Optional exception object for stack trace

### `load_upload_history() -> list`
Loads upload history from JSON file.

**Returns**: List of upload history entries

### `save_upload_history(history: list) -> None`
Saves upload history to JSON file.

**Parameters**:
- `history`: List of history entries

### `add_upload_to_history(...) -> None`
Adds an upload entry to history.

**Parameters**:
- `filename: str` - Video filename
- `youtube_id: str | None` - YouTube video ID
- `scheduled_time: datetime` - Scheduled publication time
- `file_size: int` - File size in bytes
- `upload_time: float` - Upload duration
- `upload_speed: float` - Upload speed
- `status: str` - Upload status ("success" or "failed")
- `error_message: str | None` - Error message if failed

### `backup_files() -> None`
Creates backup of important files (config, history).

**Backup Location**: `backups/` directory

**Backup Format**: `{filename}_{timestamp}.{ext}`

### `main() -> None`
Main entry point. Prevents concurrent executions and calls `_main_impl()`.

### `_main_impl() -> None`
Internal main implementation (called within lock).

**Workflow**:
1. Load configuration
2. Parse arguments
3. Validate inputs
4. Find video files
5. Authenticate (if not dry-run)
6. Process videos
7. Manage playlists (if configured)
8. Save history
9. Print summary

## Configuration Structure

### `config.json` Schema
```json
{
  "default_timezone": "string",           // Timezone (e.g., "America/Sao_Paulo")
  "default_hour_slots": [int, ...],      // Hour slots (0-23)
  "default_category_id": "string",       // YouTube category ID
  "default_start_date": "string",        // Start date (YYYY-MM-DD, optional)
  "video_extensions": [string, ...],      // Allowed video extensions
  "privacy_status": "string",            // "private", "unlisted", or "public"
  "schedule_mode": "string",              // "daily" (default) or "weekly"
  "schedule_day": "string",               // Day name for weekly mode
  "schedule_hour": int,                   // Hour for weekly mode (0-23)
  "playlist_id": "string",                // Existing playlist ID (optional)
  "create_playlist": bool,                // Create new playlist (optional)
  "playlist_title": "string"              // Playlist title (if creating)
}
```

## Error Handling

### Error Logging
All errors are logged to:
- **Console**: Immediate feedback
- **error_log.txt**: Persistent log with timestamps and stack traces

### Error Types
- **FileNotFoundError**: Missing files (credentials, clips folder)
- **ValueError**: Invalid input (date format, timezone, hour slots)
- **RuntimeError**: Concurrent execution detected
- **Exception**: General errors during upload

## Data Structures

### Upload History Entry
```python
{
    "timestamp": "ISO datetime string",
    "filename": "string",
    "youtube_id": "string | None",
    "scheduled_time": "ISO datetime string",
    "scheduled_time_readable": "string",
    "file_size_bytes": int,
    "file_size_readable": "string",
    "upload_time_seconds": float,
    "upload_time_readable": "string",
    "upload_speed_bytes_per_second": float,
    "upload_speed_readable": "string",
    "status": "success | failed",
    "error_message": "string | None"
}
```

### Execution Summary
```python
{
    "type": "execution_summary",
    "execution_timestamp": "ISO datetime string",
    "execution_date": "string",
    "total_videos": int,
    "successful_uploads": int,
    "failed_uploads": int,
    "total_uploaded_size_bytes": int,
    "total_uploaded_size_readable": "string",
    "total_upload_time_seconds": float,
    "total_upload_time_readable": "string",
    "average_speed_bytes_per_second": float,
    "average_speed_readable": "string"
}
```

## Scheduling Logic

### Daily Mode (Default)
- Videos distributed across consecutive days
- Multiple videos per day based on `hour_slots`
- Example: `[8, 18]` with 5 videos → Day 1: 8:00, 18:00; Day 2: 8:00, 18:00; Day 3: 8:00

### Weekly Mode
- All videos scheduled for the same weekday
- Each video on a different week
- Example: Monday 10:00 → Video 1: Week 1, Video 2: Week 2, etc.

## File Organization

### Expected Structure
```
project/
├── youtube_bulk_scheduler.py
├── config.json
├── client_secret.json
├── token.json
├── clips/
│   ├── video1.mp4
│   ├── video1.srt      # Optional subtitle
│   ├── video1.png      # Optional thumbnail
│   └── video2.mp4
└── sent/                # Auto-created
    └── video1.mp4       # Moved after upload
```

## Type Hints

All functions include type hints for:
- Parameters
- Return values
- Complex types use `Any` for external library objects

## Thread Safety

- **File Locking**: Prevents concurrent script executions
- **Atomic Operations**: File moves and writes are atomic where possible
- **Error Recovery**: Continues processing other videos if one fails

