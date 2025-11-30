"""
Bulk Uploader - Upload to YouTube

This module provides functions to upload videos to YouTube.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).parent.resolve()
YOUTUBE_SCRIPT = SCRIPT_DIR / "youtube_bulk_scheduler.py"


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
