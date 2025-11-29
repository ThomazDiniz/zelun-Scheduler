# YouTube Bulk Video Scheduler

A Python script to automatically upload and schedule multiple videos to your YouTube channel. The script processes videos from a local folder, uploads them to YouTube, schedules them for publication at specified times, and organizes uploaded videos into a "sent" folder.

> 🇧🇷 **Português (Brasil)**: [README.pt-BR.md](README.pt-BR.md)

## Features

- ✅ **Bulk Upload**: Process multiple videos in one run
- ✅ **Automatic Scheduling**: Schedule videos for consecutive days at configurable times
- ✅ **Quota Management**: Automatically checks YouTube API quota reset times
- ✅ **Error Handling**: Graceful error handling with clear messages
- ✅ **Relative Paths**: Uses script-relative paths for portability
- ✅ **Configurable**: Command-line arguments for all settings
- ✅ **English Codebase**: Fully documented in English

## Limitations

- **Daily Upload Limit**: YouTube API has a quota limit of 6 videos per day
- The script will automatically stop when the daily limit is reached
- Quota resets at 05:00 local time (when using Brazil timezone)

## Requirements

- Python 3.7 or higher
- Google Cloud Project with YouTube Data API v3 enabled
- OAuth 2.0 credentials from Google Cloud Console
- Video files in a `clips` folder

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Google Cloud credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the **YouTube Data API v3**
   - Create **OAuth 2.0 credentials** (Desktop application type)
   - Download the credentials JSON file
   - Rename it to `client_secret.json` and place it in the script directory
   - See `client_secret_sample.json` for the expected format

4. **Create folder structure**:
   ```
   youtube-bulk-scheduler/
   ├── youtube_bulk_scheduler.py
   ├── client_secret.json          # Your credentials (not in git)
   ├── clips/                      # Place videos here
   │   ├── video1.mp4
   │   └── video2.mp4
   └── sent/                       # Uploaded videos moved here (auto-created)
   ```

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

### Complete Examples

**Example 1**: Custom start date with default time slots
```bash
python youtube_bulk_scheduler.py --start-date 2025-12-15
```

**Example 2**: Custom timezone and time slots
```bash
python youtube_bulk_scheduler.py --timezone America/New_York --hour-slots 10 14 18
```

**Example 3**: Full customization
```bash
python youtube_bulk_scheduler.py \
  --start-date 2025-12-01 \
  --timezone America/Sao_Paulo \
  --hour-slots 8 12 16 20 \
  --category-id 20
```

**Example 4**: One video per day at noon
```bash
python youtube_bulk_scheduler.py --hour-slots 12
```

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
4. **Upload**: Each video is uploaded as private and scheduled for publication
5. **File Organization**: Successfully uploaded videos are moved to `sent/` folder

### Authentication

1. First run: The script opens a browser for OAuth authentication
2. After authentication: A `token.json` file is created (automatically ignored by git)
3. Subsequent runs: Uses the saved token (refreshes automatically if expired)

### Quota Management

- YouTube API has a daily quota limit (typically 6 uploads per day)
- The script checks if quota has reset (05:00 local time)
- If quota is exceeded, the script stops and shows a message
- Resume by running the script again after quota reset

## Project Structure

```
youtube-bulk-scheduler/
├── youtube_bulk_scheduler.py   # Main script
├── requirements.txt             # Python dependencies
├── README.md                    # This file (English)
├── README.pt-BR.md             # This file (Portuguese)
├── .gitignore                   # Git ignore rules
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

## Code Overview

### Key Functions

- **`parse_arguments()`**: Parses command-line arguments with defaults
- **`parse_start_date()`**: Handles date parsing with validation
- **`quota_reset_ok()`**: Checks if YouTube API quota has reset
- **`get_authenticated_service()`**: Handles OAuth authentication
- **`upload_and_schedule()`**: Uploads video and sets publish time
- **`main()`**: Orchestrates the entire upload process

### Configuration Constants

- **`SCOPES`**: YouTube API scope for video uploads
- **`SCRIPT_DIR`**: Directory where script is located (for relative paths)
- **`CLIPS_FOLDER`**: Path to folder containing videos (`script_dir/clips`)
- **`SENT_FOLDER`**: Path to folder for uploaded videos (`script_dir/sent`)

### Error Handling

The script includes comprehensive error handling:

- Missing `client_secret.json`: Clear instructions on how to obtain it
- Missing `clips/` folder: Explains where to create it
- Invalid timezone: Lists common timezones and provides link to full list
- Invalid date format: Explains expected format
- Invalid hour slots: Validates range (0-23)
- Quota exceeded: Stops gracefully with reset time information

## Troubleshooting

### "client_secret.json not found"
- Download OAuth credentials from Google Cloud Console
- Save as `client_secret.json` in the script directory
- See `client_secret_sample.json` for format reference

### "Clips folder not found"
- Create a `clips` folder in the same directory as the script
- Place your video files in the `clips` folder

### "Invalid timezone"
- Use a valid timezone from the [tz database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
- Common format: `Continent/City` (e.g., `America/Sao_Paulo`)

### "Daily quota exceeded"
- YouTube API allows ~6 uploads per day
- Wait until 05:00 local time for quota reset
- Run the script again after reset

### Authentication errors
- Delete `token.json` and re-authenticate
- Check that `client_secret.json` is valid
- Ensure YouTube Data API v3 is enabled in Google Cloud Console

## Security Notes

- **Never commit credentials**: `token.json` and `client_secret.json` are in `.gitignore`
- **Keep credentials private**: These files contain sensitive OAuth information
- **Use sample files**: Commit `*_sample.json` files as templates only

## License

This project is provided as-is for personal use.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your Google Cloud Console settings
3. Ensure all dependencies are installed correctly

