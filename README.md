# Zelun Scheduler

A Python script to automatically upload and schedule multiple videos to your YouTube channel. The script processes videos from a local folder, uploads them to YouTube, schedules them for publication at specified times, and organizes uploaded videos.

> 🇧🇷 **Português (Brasil)**: [README.pt-BR.md](README.pt-BR.md)

## Table of Contents

- [Features](#features)
- [Limitations](#limitations)
- [Requirements](#requirements)
- [Installation](#installation)
  - [YouTube Setup](#youtube-setup)
- [Configuration](#configuration)
  - [Configuration Options](#configuration-options)
  - [Configuration Examples](#configuration-examples)
- [Usage](#usage)
  - [Basic Usage](#basic-usage-all-defaults)
  - [Command-Line Arguments](#command-line-arguments)
  - [Complete Examples](#complete-examples)
  - [Common Use Cases](#common-use-cases)
- [How It Works](#how-it-works)
  - [Video Processing Flow](#video-processing-flow)
  - [Authentication](#authentication)
  - [Quota Management](#quota-management)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
  - [Module Overview](#module-overview)
  - [Constants](#constants)
  - [Core Functions](#core-functions)
  - [Data Structures](#data-structures)
  - [Scheduling Logic](#scheduling-logic)
  - [Error Handling](#error-handling)
- [Troubleshooting](#troubleshooting)
  - [YouTube Issues](#youtube-issues)
  - [General Issues](#general-issues)
- [Security Notes](#security-notes)
- [License](#license)
- [Support](#support)

## Features

- ✅ **YouTube Upload**: Upload videos to your YouTube channel
- ✅ **Bulk Upload**: Process multiple videos in one run
- ✅ **Automatic Scheduling**: Schedule videos for consecutive days at configurable times
- ✅ **File Organization**: Automatically moves uploaded videos to `sent/` folder
- ✅ **Quota Management**: Automatically checks API quota limits
- ✅ **Error Handling**: Graceful error handling with clear messages
- ✅ **Relative Paths**: Uses script-relative paths for portability
- ✅ **Configurable**: Command-line arguments for all settings
- ✅ **GUI Interface**: User-friendly graphical interface for easy operation
- ✅ **Dry-Run Mode**: Preview uploads before actually executing
- ✅ **English Codebase**: Fully documented in English

## Limitations

### YouTube
- **Daily Upload Limit**: YouTube API has a quota limit of ~6 videos per day (varies)
- The script will automatically stop when the daily limit is reached
- Quota resets at 05:00 local time (when using Brazil timezone)

## Requirements

- Python 3.7 or higher
- **For YouTube**: Google Cloud Project with YouTube Data API v3 enabled
- OAuth 2.0 credentials for YouTube
- Video files in a `clips` folder

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up platform credentials** (see sections below for each platform)

4. **Configure default settings (optional)**:
   - Edit `config.json` with your preferred default settings
   - The file comes with sensible defaults for Brazil timezone
   - This allows you to skip command-line arguments on every run
   - See [Configuration Examples](#configuration-examples) section below for examples

5. **Create folder structure**:
   ```
   zelun-scheduler/
   ├── youtube_bulk_scheduler.py
   ├── gui_wrapper.py
   ├── client_secret.json          # YouTube credentials (not in git)
   ├── clips/                      # Place videos here
   │   ├── video1.mp4
   │   └── video2.mp4
   └── sent/                       # Uploaded videos moved here (auto-created)
   ```

### YouTube Setup

1. **Set up Google Cloud credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the **YouTube Data API v3**
   - Create **OAuth 2.0 credentials** (Desktop application type)
   - Download the credentials JSON file
   - Rename it to `client_secret.json` and place it in the script directory
   - See `client_secret_sample.json` for the expected format

2. **First authentication**:
   - Run the script - it will open a browser for OAuth authentication
   - Authorize the application
   - Token will be saved in `token.json` for future use

**⚠️ IMPORTANT**: The credential file (`client_secret.json`) is in `.gitignore` and will NOT be committed to git.

## Configuration

The `config.json` file contains default values for the script. You can edit it to customize your preferences without passing command-line arguments every time.

Edit `config.json` with your preferences:
   ```json
   {
     "default_timezone": "America/Sao_Paulo",
     "default_hour_slots": [8, 18],
     "default_category_id": "20",
     "quota_reset_hour": 5,
     "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
     "privacy_status": "private"
   }
   ```

**Note**: Command-line arguments always override config file values.

### Configuration Options

- **`default_timezone`**: Default timezone for scheduling (e.g., `"America/Sao_Paulo"`)
- **`default_hour_slots`**: Default hour slots per day (array of integers, 0-23)
- **`default_category_id`**: Default YouTube category ID (string)
- **`quota_reset_hour`**: Hour when YouTube quota resets (0-23, default: 5)
- **`video_extensions`**: List of video file extensions to process
- **`privacy_status`**: Default privacy status (`"private"`, `"unlisted"`, or `"public"`)
- **`description`**: Default description for all videos (string, optional)
- **`tags`**: Default tags for all videos (array of strings, optional)
- **`schedule_mode`**: Scheduling mode - `"daily"` (default) or `"weekly"`
- **`schedule_day`**: Day of week for weekly mode (`"monday"`, `"tuesday"`, etc.)
- **`schedule_hour`**: Hour for weekly mode (0-23)
- **`playlist_id`**: Existing playlist ID to add videos to (optional)
- **`create_playlist`**: Create new playlist (boolean, optional)
- **`playlist_title`**: Title for new playlist (if creating)

### Configuration Examples

#### 🇧🇷 Brazil (Default)

```json
{
  "default_timezone": "America/Sao_Paulo",
  "default_hour_slots": [8, 18],
  "default_category_id": "20",
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
  "privacy_status": "private",
  "description": "",
  "tags": []
}
```

**Characteristics:**
- Timezone: GMT-3 (Brazil)
- Time slots: 8:00 and 18:00 (morning and afternoon)

#### 🇺🇸 United States - East Coast

```json
{
  "default_timezone": "America/New_York",
  "default_hour_slots": [10, 18],
  "default_category_id": "20",
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
  "privacy_status": "private"
}
```

**Characteristics:**
- Timezone: EST/EDT (GMT-5/-4)
- Time slots: 10:00 and 18:00

#### 🇺🇸 United States - West Coast

```json
{
  "default_timezone": "America/Los_Angeles",
  "default_hour_slots": [9, 17],
  "default_category_id": "20",
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
  "privacy_status": "private"
}
```

**Characteristics:**
- Timezone: PST/PDT (GMT-8/-7)
- Time slots: 9:00 and 17:00

#### 🇬🇧 United Kingdom

```json
{
  "default_timezone": "Europe/London",
  "default_hour_slots": [12, 20],
  "default_category_id": "20",
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
  "privacy_status": "private"
}
```

**Characteristics:**
- Timezone: GMT/BST (GMT+0/+1)
- Time slots: 12:00 and 20:00

#### 🇯🇵 Japan

```json
{
  "default_timezone": "Asia/Tokyo",
  "default_hour_slots": [19, 22],
  "default_category_id": "20",
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
  "privacy_status": "private"
}
```

**Characteristics:**
- Timezone: JST (GMT+9)
- Time slots: 19:00 and 22:00 (prime time)

#### 📺 Multiple Videos Per Day

```json
{
  "default_timezone": "America/Sao_Paulo",
  "default_hour_slots": [8, 12, 16, 20],
  "default_category_id": "20",
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
  "privacy_status": "private"
}
```

**Characteristics:**
- 4 videos per day: 8:00, 12:00, 16:00, 20:00
- Ideal for channels with high publishing frequency

#### 🎮 Specific Category (Music)

```json
{
  "default_timezone": "America/Sao_Paulo",
  "default_hour_slots": [8, 18],
  "default_category_id": "10",
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
  "privacy_status": "private"
}
```

**Common categories:**
- `1` - Film & Animation
- `10` - Music
- `20` - Gaming (default)
- `22` - People & Blogs
- `23` - Comedy
- `24` - Entertainment

#### 🔓 Public Videos

```json
{
  "default_timezone": "America/Sao_Paulo",
  "default_hour_slots": [8, 18],
  "default_category_id": "20",
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
  "privacy_status": "public"
}
```

**Privacy options:**
- `"private"` - Only you can see
- `"unlisted"` - Anyone with the link can see
- `"public"` - Visible to everyone

#### 📅 Custom Start Date

```json
{
  "default_timezone": "America/Sao_Paulo",
  "default_hour_slots": [8, 18],
  "default_category_id": "20",
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
  "privacy_status": "private",
  "default_start_date": "2025-12-01"
}
```

**Format:** `YYYY-MM-DD` (e.g., `"2025-12-01"` for December 1st, 2025)

**How it works:**
- If `default_start_date` is set, videos will be scheduled starting from that date
- If not set (or `null`), videos will start from today's date
- You can override this for a specific run using: `--start-date 2025-12-15`

#### 📆 Weekly Scheduling

```json
{
  "default_timezone": "America/Sao_Paulo",
  "default_category_id": "20",
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
  "privacy_status": "private",
  "schedule_mode": "weekly",
  "schedule_day": "monday",
  "schedule_hour": 12
}
```

**Characteristics:**
- `schedule_mode`: Set to `"weekly"` (default is `"daily"`)
- `schedule_day`: Day of the week (`"monday"`, `"tuesday"`, `"wednesday"`, `"thursday"`, `"friday"`, `"saturday"`, `"sunday"`)
- `schedule_hour`: Hour of the day (0-23, e.g., `12` for 12:00 PM)

**How it works:**
- The script automatically finds the **next occurrence** of the specified day from today
- Each video is scheduled for consecutive weeks on the same day and time
- No need to specify a start date - it starts from the next available day

#### 📝 With Description and Tags

```json
{
  "default_timezone": "America/Sao_Paulo",
  "default_hour_slots": [8, 18],
  "default_category_id": "20",
  "privacy_status": "private",
  "description": "Check out my gaming videos!\n\nSubscribe for more content.",
  "tags": ["gaming", "hollow knight", "indie games"]
}
```

**Note:** Description and tags will be applied to all videos in the batch.

## Usage

### Basic Usage (All Defaults)

Run with default settings:
- Start date: Today
- Timezone: GMT Brazil (America/Sao_Paulo)
- Time slots: 8:00 AM and 6:00 PM (2 videos per day)
- Category: Gaming (ID: 20)

```bash
python youtube_bulk_scheduler.py
```

### Command-Line Arguments

All parameters can be customized via command-line arguments:

#### `--start-date` (Optional)
Start date for the first video in `YYYY-MM-DD` format. Defaults to today.

```bash
python youtube_bulk_scheduler.py --start-date 2025-12-01
```

#### `--timezone` (Optional)
Timezone for scheduling. Default: `America/Sao_Paulo` (GMT Brazil)

Common timezones:
- `America/Sao_Paulo` - Brazil (GMT-3)
- `America/New_York` - Eastern Time (GMT-5/4)
- `Europe/London` - UK (GMT+0/1)
- `Asia/Tokyo` - Japan (GMT+9)

```bash
python youtube_bulk_scheduler.py --timezone America/New_York
```

#### `--hour-slots` (Optional)
Hour slots per day (24-hour format). Default: `8 18` (8 AM and 6 PM)

```bash
# One video per day at 10 AM
python youtube_bulk_scheduler.py --hour-slots 10

# Three videos per day at 9 AM, 12 PM, and 6 PM
python youtube_bulk_scheduler.py --hour-slots 9 12 18

# Four videos per day
python youtube_bulk_scheduler.py --hour-slots 8 12 16 20
```

#### `--category-id` (Optional)
YouTube category ID. Default: `20` (Gaming)

Common categories:
- `1` - Film & Animation
- `2` - Autos & Vehicles
- `10` - Music
- `15` - Pets & Animals
- `17` - Sports
- `19` - Travel & Events
- `20` - Gaming
- `22` - People & Blogs
- `23` - Comedy
- `24` - Entertainment
- `25` - News & Politics
- `26` - Howto & Style
- `27` - Education
- `28` - Science & Technology

```bash
python youtube_bulk_scheduler.py --category-id 24
```

#### `--description` (Optional)
Global description for all videos. Default: empty string (from config).

```bash
python youtube_bulk_scheduler.py --description "Check out my videos!\n\nSubscribe for more content."
```

#### `--tags` (Optional)
Tags for all videos (comma-separated). Default: empty (from config).

```bash
python youtube_bulk_scheduler.py --tags "gaming, hollow knight, indie games"
```

#### `--dry-run` (Optional)
Preview what would be uploaded without actually uploading.

```bash
python youtube_bulk_scheduler.py --dry-run
```

This is useful to:
- Check if titles are valid
- See the scheduling plan
- Verify file sizes
- Test before actual upload

### Complete Examples

**Example 1**: Custom start date with default time slots
```bash
python youtube_bulk_scheduler.py --start-date 2025-12-15
```

**Example 2**: Custom timezone and time slots
```bash
python youtube_bulk_scheduler.py --timezone America/New_York --hour-slots 10 14 18
```

**Example 3**: Full customization with description and tags
```bash
python youtube_bulk_scheduler.py \
  --start-date 2025-12-01 \
  --timezone America/Sao_Paulo \
  --hour-slots 8 12 16 20 \
  --category-id 20 \
  --description "My gaming videos" \
  --tags "gaming, indie, hollow knight"
```

**Example 4**: One video per day at noon
```bash
python youtube_bulk_scheduler.py --hour-slots 12
```

**Example 5**: Preview before uploading
```bash
python youtube_bulk_scheduler.py --dry-run
```

### Common Use Cases

#### Use Case 1: Daily Upload Schedule
**Goal**: Upload 2 videos per day for a week

**Setup**:
1. Place 14 videos in `clips/` folder
2. Run: `python youtube_bulk_scheduler.py --hour-slots 8 18`

**Result**: 
- Day 1: Videos 1-2 at 8:00 and 18:00
- Day 2: Videos 3-4 at 8:00 and 18:00
- ... and so on

#### Use Case 2: Weekly Series
**Goal**: Upload one video every Monday at 10 AM

**Setup**:
1. Edit `config.json`:
   ```json
   {
     "schedule_mode": "weekly",
     "schedule_day": "monday",
     "schedule_hour": 10
   }
   ```
2. Place videos in `clips/` folder
3. Run: `python youtube_bulk_scheduler.py`

**Result**: Each video scheduled for consecutive Mondays at 10:00 AM

#### Use Case 3: Videos with Subtitles and Thumbnails
**Goal**: Upload videos with accessibility features

**Setup**:
1. Organize files:
   ```
   clips/
     video1.mp4
     video1.srt        # Subtitles
     video1.png        # Thumbnail
     video2.mp4
     video2.srt
     video2.png
   ```
2. Run: `python youtube_bulk_scheduler.py`

**Result**: Videos uploaded with subtitles and custom thumbnails

**Note**: 
- Subtitle files: `.srt` or `.vtt` format, same name as video
- Thumbnail files: `.png` format, same name as video
- Language detection: If subtitle filename contains language code (e.g., `video.pt-BR.srt`), it will be detected automatically

## How It Works

### Video Processing Flow

1. **Script Execution**: The script runs from its directory location
2. **Video Discovery**: Scans the `clips/` folder for video files
3. **Scheduling Logic**: 
   - Videos are scheduled starting from the `--start-date` (or today)
   - Videos are distributed across days based on `--hour-slots`
   - Example: With slots `[8, 18]` and 5 videos:
     - Video 1: Day 1 at 8:00
     - Video 2: Day 1 at 18:00
     - Video 3: Day 2 at 8:00
     - Video 4: Day 2 at 18:00
     - Video 5: Day 3 at 8:00
4. **Upload**: Each video is uploaded to YouTube and scheduled for publication
5. **File Organization**: Videos are moved to `sent/` folder after successful upload

### Authentication

#### YouTube
1. First run: The script opens a browser for OAuth authentication
2. After authentication: A `token.json` file is created (automatically ignored by git)
3. Subsequent runs: Uses the saved token (refreshes automatically if expired)

### Quota Management

#### YouTube
- YouTube API has a daily quota limit (typically ~6 uploads per day, varies)
- The script checks if quota has reset (05:00 local time)
- If quota is exceeded, the script stops and shows a message
- Resume by running the script again after quota reset


## Project Structure

```
zelun-scheduler/
├── youtube_bulk_scheduler.py   # Main script
├── requirements.txt             # Python dependencies
├── README.md                    # This file (English - includes all documentation)
├── README.pt-BR.md             # This file (Portuguese)
├── .gitignore                   # Git ignore rules
├── config.json                  # Default configuration (editable)
├── client_secret.json          # Your OAuth credentials (not in git)
├── token.json                  # OAuth token cache (not in git)
├── client_secret_sample.json   # Sample credentials format
├── token_sample.json           # Sample token format
├── clips/                      # Video files to upload
│   ├── video1.mp4
│   └── video2.mp4
└── sent/                       # Successfully uploaded videos
    └── video1.mp4
```

## API Documentation

Technical documentation for developers and advanced users.

### Module Overview

The script is organized into several functional modules:

- **Configuration Management**: Loading and parsing configuration files
- **Authentication**: OAuth 2.0 authentication with YouTube API
- **Video Processing**: Upload, scheduling, and metadata management
- **File Management**: Handling videos, subtitles, thumbnails
- **History & Logging**: Recording upload history and errors
- **Utilities**: Helper functions for formatting and validation

### Constants

#### File Paths
```python
SCRIPT_DIR: Path              # Script directory
CLIPS_FOLDER: Path            # Input videos folder
SENT_FOLDER: Path             # Uploaded videos folder
CLIENT_SECRETS_FILE: Path     # OAuth credentials
TOKEN_FILE: Path              # OAuth token cache
CONFIG_FILE: Path             # Configuration file
HISTORY_FILE: Path            # Upload history (logs/upload_history.json)
ERROR_LOG_FILE: Path          # Error log (logs/error_log.txt)
LOCK_FILE: Path               # Lock file for concurrency
BACKUP_DIR: Path              # Backup directory
LOGS_DIR: Path                # Logs directory
```

#### API Scopes
```python
SCOPES: list[str] = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]
```

### Core Functions

#### `load_config() -> dict`
Loads configuration from `config.json` or returns defaults.

**Returns**: Dictionary with configuration values

**Default Config**:
```python
{
    "default_timezone": "America/Sao_Paulo",
    "default_hour_slots": [8, 18],
    "default_category_id": "20",
    "video_extensions": [".mp4", ".mov", ".avi", ...],
    "privacy_status": "private",
    "description": "",
    "tags": []
}
```

#### `parse_arguments(config: dict) -> argparse.Namespace`
Parses command-line arguments with defaults from config.

**Arguments**:
- `--start-date`: Start date (YYYY-MM-DD)
- `--timezone`: Timezone string
- `--hour-slots`: List of hour slots (0-23)
- `--category-id`: YouTube category ID
- `--description`: Description for all videos
- `--tags`: Tags for all videos (comma-separated)
- `--dry-run`: Preview mode flag

#### `sanitize_title(title: str) -> tuple[str, list[str]]`
Sanitizes video title by removing invalid characters.

**Returns**: Tuple of (sanitized_title, warnings_list)

**Behavior**:
- Removes invalid characters (`<`, `>`)
- Truncates if over 100 characters
- Returns warnings for any issues

#### `format_file_size(size_bytes: int) -> str`
Formats file size in human-readable format.

**Example**: `524288000` → `"500.00 MB"`

#### `format_duration(seconds: float) -> str`
Formats duration in human-readable format.

**Example**: `3661.5` → `"1h 1m 1s"`

#### `find_related_files(video_path: Path) -> dict[str, Path | None]`
Finds related files (subtitles, thumbnails) for a video.

**Returns**: Dictionary with keys:
- `'subtitle'`: Path to `.srt` or `.vtt` file (if exists)
- `'thumbnail'`: Path to `.png` file (if exists)

**File Naming**:
- Subtitle: `{video_name}.srt` or `{video_name}.vtt`
- Thumbnail: `{video_name}.png`
- Language codes: `{video_name}.{lang}.srt` (e.g., `video.pt-BR.srt`)

#### `get_authenticated_service(client_secrets_path: Path, token_path: Path, show_status: bool = True) -> Any`
Authenticates with YouTube API using OAuth 2.0.

**Behavior**:
- Loads cached token if available
- Refreshes expired tokens automatically
- Opens browser for first-time authentication
- Saves token for future use
- Handles invalid scope errors by re-authenticating

#### `upload_and_schedule(...) -> dict[str, Any]`
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
- `description: str` - Description for the video
- `tags: list[str]` - Tags for the video

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
- Stops execution if upload limit exceeded

#### `file_lock(lock_path: Path) -> contextmanager`
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

#### `log_error(error_message: str, error_type: str = "ERROR", exception: Exception | None = None) -> None`
Logs error to both console and error log file.

**Parameters**:
- `error_message`: Error message string
- `error_type`: Type of error ("ERROR", "WARNING", etc.)
- `exception`: Optional exception object for stack trace

#### `load_upload_history() -> list`
Loads upload history from JSON file.

**Returns**: List of upload history entries

#### `save_upload_history(history: list) -> None`
Saves upload history to JSON file.

#### `add_upload_to_history(...) -> None`
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

#### `backup_files() -> None`
Creates backup of important files (config, history) by appending to single files.

**Backup Location**: `backups/` directory

**Backup Format**: 
- `config_backup.json` - Single file with JSON Lines format (one backup entry per line)
- `history_backup.json` - Single file with JSON Lines format (one backup entry per line)

Each line contains a JSON object with `timestamp` and `data` fields.

#### `main() -> None`
Main entry point. Prevents concurrent executions and calls `_main_impl()`.

#### `_main_impl() -> None`
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

### Data Structures

#### Upload History Entry
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

#### Execution Summary
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

### Scheduling Logic

#### Daily Mode (Default)
- Videos distributed across consecutive days
- Multiple videos per day based on `hour_slots`
- Example: `[8, 18]` with 5 videos → Day 1: 8:00, 18:00; Day 2: 8:00, 18:00; Day 3: 8:00

#### Weekly Mode
- All videos scheduled for the same weekday
- Each video on a different week
- Example: Monday 10:00 → Video 1: Week 1, Video 2: Week 2, etc.

### Error Handling

#### Error Logging
All errors are logged to:
- **Console**: Immediate feedback
- **logs/error_log.txt**: Persistent log with timestamps and stack traces

#### Error Types
- **FileNotFoundError**: Missing files (credentials, clips folder)
- **ValueError**: Invalid input (date format, timezone, hour slots)
- **RuntimeError**: Concurrent execution detected
- **ResumableUploadError**: Upload errors (including upload limit exceeded)
- **HttpError**: HTTP errors from YouTube API
- **Exception**: General errors during upload

### Thread Safety

- **File Locking**: Prevents concurrent script executions
- **Atomic Operations**: File moves and writes are atomic where possible
- **Error Recovery**: Continues processing other videos if one fails
- **Upload Limit Detection**: Automatically stops when daily upload limit is exceeded

### Type Hints

All functions include type hints for:
- Parameters
- Return values
- Complex types use `Any` for external library objects

### Error Handling

The script includes comprehensive error handling:

- Missing `client_secret.json`: Clear instructions on how to obtain it
- Missing `clips/` folder: Explains where to create it
- Invalid timezone: Lists common timezones and provides link to full list
- Invalid date format: Explains expected format
- Invalid hour slots: Validates range (0-23)
- Upload limit exceeded: Stops execution immediately when daily limit is reached

## Troubleshooting

### YouTube Issues

#### "client_secret.json not found"
- Download OAuth credentials from Google Cloud Console
- Save as `client_secret.json` in the script directory
- See `client_secret_sample.json` for format reference

#### "Daily quota exceeded"
- YouTube API allows ~6 uploads per day (varies)
- Wait until 05:00 local time for quota reset
- Run the script again after reset

#### YouTube Authentication errors
- Delete `token.json` and re-authenticate
- Check that `client_secret.json` is valid
- Ensure YouTube Data API v3 is enabled in Google Cloud Console

### General Issues

#### "Clips folder not found"
- Create a `clips` folder in the same directory as the script
- Place your video files in the `clips` folder

#### "Invalid timezone"
- Use a valid timezone from the [tz database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
- Common format: `Continent/City` (e.g., `America/Sao_Paulo`)

#### Video not being moved to sent folder
- Files are automatically moved to `sent/` folder after successful upload
- If a file wasn't moved, check if the upload completed successfully

## Security Notes

- **Never commit credentials**: `token.json` and `client_secret.json` are in `.gitignore`
- **Keep credentials private**: These files contain sensitive OAuth information
- **Use sample files**: Commit `*_sample.json` files as templates only
- **Config file**: `config.json` is committed as it only contains non-sensitive preferences

## License

This project is provided as-is for personal use.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your Google Cloud Console settings
3. Ensure all dependencies are installed correctly

