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
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Required scope for video uploads
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
CLIPS_FOLDER = SCRIPT_DIR / "clips"
SENT_FOLDER = SCRIPT_DIR / "sent"
CLIENT_SECRETS_FILE = SCRIPT_DIR / "client_secret.json"
TOKEN_FILE = SCRIPT_DIR / "token.json"


def parse_arguments():
    """Parse command-line arguments with default values."""
    parser = argparse.ArgumentParser(
        description="Upload and schedule videos to YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use all default values (today's date, GMT Brazil, 8am and 6pm slots)
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
        default="America/Sao_Paulo",  # GMT Brazil
        help="Timezone for scheduling (e.g., 'America/Sao_Paulo', 'America/New_York'). Default: America/Sao_Paulo (GMT Brazil)"
    )

    parser.add_argument(
        "--hour-slots",
        type=int,
        nargs="+",
        default=[8, 18],
        help="Hour slots per day (24-hour format). Default: 8 18 (8am and 6pm). Example: --hour-slots 10 14 18"
    )

    parser.add_argument(
        "--category-id",
        type=str,
        default="20",
        help="YouTube category ID. Default: 20 (Gaming). See README for category list."
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


def quota_reset_ok(timezone: ZoneInfo) -> bool:
    """
    Returns True if current time has passed quota reset time (05:00 local time).
    YouTube quota resets at 00:00 PT, which is 05:00 in Brazil (UTC-3).
    """
    now = datetime.now(timezone)
    reset_time = now.replace(hour=5, minute=0, second=0, microsecond=0)
    return now >= reset_time


def get_authenticated_service(client_secrets_path: Path, token_path: Path):
    """Authenticate using OAuth with client_secret.json."""
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
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

            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secrets_path), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(token_path, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_and_schedule(
    video_path: Path,
    publish_time: datetime,
    youtube,
    category_id: str
) -> None:
    """Upload a video and schedule it for publication."""
    title = video_path.stem
    description = ""

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": "private",
            "publishAt": publish_time.isoformat(),
        },
    }

    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = request.execute()
    print(
        f"Video '{title}' uploaded! ID={response.get('id')} "
        f"— Scheduled for {publish_time.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )


def main() -> None:
    """Main function to orchestrate video uploads."""
    args = parse_arguments()

    # Validate and parse timezone
    try:
        timezone = ZoneInfo(args.timezone)
    except Exception as e:
        print(f"\n❌ ERROR: Invalid timezone '{args.timezone}'\n")
        print(f"Common timezones: America/Sao_Paulo, America/New_York, Europe/London, Asia/Tokyo")
        print(f"See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones")
        sys.exit(1)

    # Validate and parse start date
    try:
        start_date = parse_start_date(args.start_date, timezone)
    except ValueError as e:
        print(f"\n❌ ERROR: {e}\n")
        sys.exit(1)

    # Validate hour slots
    if not args.hour_slots:
        print("\n❌ ERROR: At least one hour slot must be specified\n")
        sys.exit(1)

    for hour in args.hour_slots:
        if not (0 <= hour < 24):
            print(f"\n❌ ERROR: Invalid hour slot '{hour}'. Must be between 0 and 23.\n")
            sys.exit(1)

    # Check quota reset
    if not quota_reset_ok(timezone):
        print("❌ YouTube daily quota has NOT reset yet.")
        print("Quota will reset at 05:00 local time.")
        print("Please run the script again after 05:00.")
        return

    print("✔ Daily quota reset confirmed. Starting uploads...\n")

    # Validate clips folder exists
    if not CLIPS_FOLDER.exists():
        raise FileNotFoundError(
            f"\n❌ ERROR: Clips folder not found: {CLIPS_FOLDER}\n"
            f"\nPlease create a 'clips' folder in the same directory as this script:\n"
            f"{SCRIPT_DIR}\n"
            f"\nPlace your video files in the 'clips' folder."
        )

    # Authenticate
    try:
        youtube = get_authenticated_service(CLIENT_SECRETS_FILE, TOKEN_FILE)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: Authentication failed: {e}\n")
        sys.exit(1)

    # Find video files
    video_extensions = {".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"}
    videos = [
        f for f in CLIPS_FOLDER.iterdir()
        if f.is_file() and f.suffix.lower() in video_extensions
    ]
    videos.sort(key=lambda x: x.name)

    if not videos:
        print(f"No videos found in: {CLIPS_FOLDER}")
        return

    print(f"Found {len(videos)} video(s) to upload.\n")

    # Create sent folder
    SENT_FOLDER.mkdir(exist_ok=True)

    base_day = start_date.date()

    # Process videos
    for idx, video_path in enumerate(videos):
        day_offset = idx // len(args.hour_slots)
        slot_index = idx % len(args.hour_slots)

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
            upload_and_schedule(video_path, publish_dt, youtube, args.category_id)

            # Move video to "sent" folder after successful upload
            new_path = SENT_FOLDER / video_path.name
            shutil.move(str(video_path), str(new_path))
            print(f"Moved to: {new_path}\n")

        except Exception as e:
            error_msg = str(e)
            print(f"Error processing {video_path.name}: {error_msg}\n")

            if "uploadLimitExceeded" in error_msg or "quotaExceeded" in error_msg:
                print("=" * 60)
                print("❌ DAILY LIMIT REACHED — Script will be interrupted.")
                print("Quota will be renewed at 05:00 local time.")
                print("=" * 60)
                return

            continue

    print(f"\n✔ Finished processing videos. {len(videos)} video(s) processed.")


if __name__ == "__main__":
    main()
