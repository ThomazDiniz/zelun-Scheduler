"""
Upload Tracking System

Tracks upload status for videos on YouTube.
Only moves files to 'sent' folder when uploaded.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

SCRIPT_DIR = Path(__file__).parent.resolve()
TRACKING_FILE = SCRIPT_DIR / "logs" / "upload_tracking.json"
SENT_FOLDER = SCRIPT_DIR / "sent"


def load_tracking() -> dict[str, Any]:
    """Load upload tracking data from JSON file."""
    TRACKING_FILE.parent.mkdir(exist_ok=True)
    
    if TRACKING_FILE.exists():
        try:
            with open(TRACKING_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                return {}
        except (json.JSONDecodeError, Exception):
            return {}
    return {}


def save_tracking(tracking_data: dict[str, Any]) -> None:
    """Save upload tracking data to JSON file."""
    TRACKING_FILE.parent.mkdir(exist_ok=True)
    
    try:
        with open(TRACKING_FILE, "w", encoding="utf-8") as f:
            json.dump(tracking_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️  WARNING: Could not save tracking data: {e}")


def get_video_status(filename: str) -> dict[str, Any]:
    """Get upload status for a specific video."""
    tracking = load_tracking()
    return tracking.get(filename, {
        "youtube": {"uploaded": False}
    })


def mark_uploaded(filename: str, platform: str, video_id: Optional[str] = None, 
                  scheduled_time: Optional[datetime] = None, error: Optional[str] = None) -> None:
    """
    Mark a video as uploaded to a platform.
    
    Args:
        filename: Name of the video file
        platform: 'youtube'
        video_id: ID of the uploaded video (if successful)
        scheduled_time: When the video is scheduled to publish
        error: Error message if upload failed
    """
    tracking = load_tracking()
    
    if filename not in tracking:
        tracking[filename] = {
            "youtube": {"uploaded": False}
        }
    
    tracking[filename][platform] = {
        "uploaded": error is None,
        "uploaded_at": datetime.now().isoformat(),
        "video_id": video_id,
        "scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
        "error": error
    }
    
    save_tracking(tracking)


def is_uploaded_to_all(filename: str, platforms: list[str]) -> bool:
    """
    Check if video has been uploaded to all specified platforms.
    
    Args:
        filename: Name of the video file
        platforms: List of platforms to check (e.g., ['youtube'])
    
    Returns:
        True if uploaded to all platforms, False otherwise
    """
    status = get_video_status(filename)
    
    for platform in platforms:
        if not status.get(platform, {}).get("uploaded", False):
            return False
    
    return True


def get_pending_videos(clips_folder: Path, platforms: list[str], 
                       video_extensions: set[str]) -> list[Path]:
    """
    Get list of videos that still need to be uploaded to at least one platform.
    
    Args:
        clips_folder: Folder containing video files
        platforms: List of platforms to check (e.g., ['youtube'])
        video_extensions: Set of valid video file extensions
    
    Returns:
        List of video paths that need uploading
    """
    if not clips_folder.exists():
        return []
    
    videos = [
        f for f in clips_folder.iterdir()
        if f.is_file() and f.suffix.lower() in video_extensions
    ]
    
    pending = []
    for video in videos:
        # Check if already uploaded to all requested platforms
        if not is_uploaded_to_all(video.name, platforms):
            pending.append(video)
    
    return sorted(pending, key=lambda x: x.name)


def should_move_to_sent(filename: str, platforms: list[str]) -> bool:
    """
    Check if video should be moved to 'sent' folder.
    Only moves when uploaded to all specified platforms.
    
    Args:
        filename: Name of the video file
        platforms: List of platforms that should have the video uploaded
    
    Returns:
        True if should move to sent, False otherwise
    """
    return is_uploaded_to_all(filename, platforms)


def move_to_sent(video_path: Path) -> None:
    """
    Move video to 'sent' folder after successful upload.
    
    Args:
        video_path: Path to the video file
    """
    SENT_FOLDER.mkdir(exist_ok=True)
    new_path = SENT_FOLDER / video_path.name
    
    try:
        import shutil
        shutil.move(str(video_path), str(new_path))
        print(f"   📦 Moved to sent folder: {video_path.name}")
    except Exception as e:
        print(f"   ⚠️  Warning: Could not move {video_path.name} to sent folder: {e}")


def get_upload_summary() -> dict[str, Any]:
    """Get summary of upload status across all videos."""
    tracking = load_tracking()
    
    total_videos = len(tracking)
    youtube_uploaded = sum(1 for v in tracking.values() if v.get("youtube", {}).get("uploaded", False))
    
    return {
        "total_videos": total_videos,
        "youtube_uploaded": youtube_uploaded,
        "not_uploaded": total_videos - youtube_uploaded
    }
