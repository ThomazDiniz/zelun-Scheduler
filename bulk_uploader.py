"""
Bulk Uploader - Upload to multiple platforms simultaneously

This module provides functions to upload videos to YouTube, TikTok, or both.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).parent.resolve()
YOUTUBE_SCRIPT = SCRIPT_DIR / "youtube_bulk_scheduler.py"
TIKTOK_SCRIPT = SCRIPT_DIR / "tiktok_bulk_scheduler.py"


def upload_to_youtube(
    start_date: str = None,
    timezone: str = "America/Sao_Paulo",
    hour_slots: list[int] = None,
    category_id: str = "20",
    description: str = "",
    tags: str = None,
    dry_run: bool = False
) -> int:
    """
    Upload videos to YouTube.
    
    Returns:
        Exit code (0 for success)
    """
    cmd = [sys.executable, str(YOUTUBE_SCRIPT)]
    
    if start_date:
        cmd.extend(["--start-date", start_date])
    
    if timezone:
        cmd.extend(["--timezone", timezone])
    
    if hour_slots:
        cmd.extend(["--hour-slots"] + [str(h) for h in hour_slots])
    
    if category_id:
        cmd.extend(["--category-id", category_id])
    
    if description:
        cmd.extend(["--description", description])
    
    if tags:
        cmd.extend(["--tags", tags])
    
    if dry_run:
        cmd.append("--dry-run")
    
    result = subprocess.run(cmd)
    return result.returncode


def upload_to_tiktok(
    start_date: str = None,
    timezone: str = "America/Sao_Paulo",
    hour_slots: list[int] = None,
    description: str = "",
    dry_run: bool = False
) -> int:
    """
    Upload videos to TikTok.
    
    Returns:
        Exit code (0 for success)
    """
    cmd = [sys.executable, str(TIKTOK_SCRIPT)]
    
    if start_date:
        cmd.extend(["--start-date", start_date])
    
    if timezone:
        cmd.extend(["--timezone", timezone])
    
    if hour_slots:
        cmd.extend(["--hour-slots"] + [str(h) for h in hour_slots])
    
    if description:
        cmd.extend(["--description", description])
    
    if dry_run:
        cmd.append("--dry-run")
    
    result = subprocess.run(cmd)
    return result.returncode


def upload_to_both(
    start_date: str = None,
    timezone: str = "America/Sao_Paulo",
    hour_slots: list[int] = None,
    category_id: str = "20",
    description: str = "",
    tags: str = None,
    dry_run: bool = False
) -> dict[str, int]:
    """
    Upload videos to both YouTube and TikTok.
    
    Returns:
        Dictionary with exit codes for each platform
    """
    results = {}
    
    # Upload to YouTube first
    print("=" * 80)
    print("📺 UPLOADING TO YOUTUBE")
    print("=" * 80)
    results['youtube'] = upload_to_youtube(
        start_date=start_date,
        timezone=timezone,
        hour_slots=hour_slots,
        category_id=category_id,
        description=description,
        tags=tags,
        dry_run=dry_run
    )
    
    # Then upload to TikTok
    print("\n" + "=" * 80)
    print("🎵 UPLOADING TO TIKTOK")
    print("=" * 80)
    results['tiktok'] = upload_to_tiktok(
        start_date=start_date,
        timezone=timezone,
        hour_slots=hour_slots,
        description=description,
        dry_run=dry_run
    )
    
    return results

