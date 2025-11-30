"""
TikTok Video Upload and Scheduler Script

This script iterates through all video files in a folder and uploads them
to your TikTok account, scheduling each video to publish on consecutive days,
with multiple videos per day (configurable time slots).

After a successful upload, the video is tracked but only moved to "sent" folder
when uploaded to all requested platforms.

Features:
- OAuth authentication with TikTok API
- Video upload with progress tracking
- Scheduling support (up to 10 days in advance)
- Configurable via command-line arguments
- Relative paths based on script location
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import time
import urllib.parse
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

# Fix encoding for Windows console to support emojis
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Platform-specific imports for file locking
if sys.platform != 'win32':
    import fcntl

import requests
import webbrowser
from tqdm import tqdm

# Import shared utilities
import upload_tracker

# Import from YouTube scheduler (shared utilities)
try:
    from youtube_bulk_scheduler import (
        SCRIPT_DIR, CLIPS_FOLDER, CONFIG_FILE, LOGS_DIR, ERROR_LOG_FILE,
        LOCK_FILE, BACKUP_DIR, load_config, log_error, format_file_size,
        format_duration, sanitize_title, add_upload_to_history, file_lock,
        backup_files, parse_start_date
    )
except ImportError:
    # Fallback if import fails
    import shutil
    from pathlib import Path
    from datetime import datetime
    from zoneinfo import ZoneInfo
    
    SCRIPT_DIR = Path(__file__).parent.resolve()
    CLIPS_FOLDER = SCRIPT_DIR / "clips"
    CONFIG_FILE = SCRIPT_DIR / "config.json"
    LOGS_DIR = SCRIPT_DIR / "logs"
    ERROR_LOG_FILE = LOGS_DIR / "error_log.txt"
    LOCK_FILE = SCRIPT_DIR / ".script.lock"
    BACKUP_DIR = SCRIPT_DIR / "backups"
    
    def load_config():
        import json
        default = {
            "default_timezone": "America/Sao_Paulo",
            "default_hour_slots": [8, 18],
            "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
            "description": ""
        }
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return {**default, **json.load(f)}
            except:
                return default
        return default
    
    def log_error(msg, error_type="ERROR", exception=None):
        print(f"[{error_type}] {msg}")
        if exception:
            import traceback
            print(traceback.format_exc())
    
    def format_file_size(size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def format_duration(seconds):
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def sanitize_title(title):
        invalid_chars = ['<', '>']
        sanitized = title
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '')
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        return sanitized, []
    
    def add_upload_to_history(*args, **kwargs):
        pass  # Placeholder
    
    def file_lock(lock_path):
        from contextlib import contextmanager
        @contextmanager
        def _lock():
            yield
        return _lock()
    
    def backup_files():
        pass
    
    def parse_start_date(date_str, timezone):
        if date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return datetime(date_obj.year, date_obj.month, date_obj.day, 0, 0, 0, tzinfo=timezone)
        return datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)

# TikTok API endpoints
TIKTOK_API_BASE = "https://open.tiktokapis.com/v2"
TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
# Default redirect URI (must match the one configured in TikTok Developer Portal)
DEFAULT_REDIRECT_URI = "http://localhost:8080/callback/"

# TikTok OAuth scopes for Content Posting API
# Required scopes:
# - user.info.basic: Read user's profile info (included in Login Kit)
# - video.upload: Share content as draft (included in Content Posting API)
# - video.publish: Directly post content (included in Content Posting API)
TIKTOK_SCOPES = [
    "user.info.basic",
    "video.upload"
]

# TikTok configuration files
TIKTOK_CLIENT_SECRETS_FILE = SCRIPT_DIR / "tiktok_client_secret.json"
TIKTOK_TOKEN_FILE = SCRIPT_DIR / "tiktok_token.json"


def generate_code_verifier() -> str:
    """
    Generate a cryptographically random code verifier for PKCE.
    
    Returns:
        A URL-safe base64-encoded random string (43-128 characters)
    """
    # Generate 32 random bytes (256 bits) and encode as base64url
    random_bytes = secrets.token_bytes(32)
    code_verifier = base64.urlsafe_b64encode(random_bytes).decode('utf-8')
    # Remove padding
    code_verifier = code_verifier.rstrip('=')
    return code_verifier


def generate_code_challenge(code_verifier: str) -> str:
    """
    Generate a code challenge from a code verifier using SHA256.
    
    Args:
        code_verifier: The code verifier string
    
    Returns:
        A URL-safe base64-encoded SHA256 hash
    """
    # Hash the code verifier with SHA256
    sha256_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    # Encode as base64url
    code_challenge = base64.urlsafe_b64encode(sha256_hash).decode('utf-8')
    # Remove padding
    code_challenge = code_challenge.rstrip('=')
    return code_challenge


def get_authenticated_token(client_secrets_path: Path, token_path: Path, show_status: bool = True) -> str:
    """
    Authenticate with TikTok API and return access token.
    
    Args:
        client_secrets_path: Path to TikTok client secrets JSON
        token_path: Path to save/load token
        show_status: Whether to print status messages
    
    Returns:
        Access token string
    """
    if show_status:
        print("🔐 Authenticating with TikTok API...")
    
    # Load saved token if exists
    if token_path.exists():
        try:
            with open(token_path, "r", encoding="utf-8") as f:
                token_data = json.load(f)
                access_token = token_data.get("access_token")
                expires_at = token_data.get("expires_at", 0)
                
                # Check if token is still valid (with 5 minute buffer)
                if access_token and expires_at > time.time() + 300:
                    if show_status:
                        print("   ✓ Using saved token")
                    return access_token
        except Exception:
            pass
    
    # Need to authenticate
    if not client_secrets_path.exists():
        raise FileNotFoundError(
            f"\n❌ ERROR: {client_secrets_path.name} not found!\n"
            f"\nThe script requires {client_secrets_path.name} for TikTok API authentication.\n"
            f"\nTo fix this:\n"
            f"1. Go to https://developers.tiktok.com/\n"
            f"2. Create an app and get your Client Key and Client Secret\n"
            f"3. Configure Redirect URI in your app settings: http://localhost:8080/callback/\n"
            f"4. Enable required scopes: user.info.basic, video.upload, and video.publish\n"
            f"5. Save credentials as '{client_secrets_path.name}' in this directory\n"
            f"6. Format: {{\"client_key\": \"your_key\", \"client_secret\": \"your_secret\", \"redirect_uri\": \"http://localhost:8080/callback/\"}}\n"
            f"\n⚠️  IMPORTANT: The redirect_uri in the file MUST match exactly the one configured in TikTok Developer Portal!\n"
        )
    
    # Load client secrets
    try:
        with open(client_secrets_path, "r", encoding="utf-8") as f:
            secrets_data = json.load(f)
            client_key = secrets_data.get("client_key")
            client_secret = secrets_data.get("client_secret")
            # Allow custom redirect_uri in config, default to localhost:8080
            redirect_uri = secrets_data.get("redirect_uri", DEFAULT_REDIRECT_URI)
    except Exception as e:
        raise ValueError(f"Failed to load TikTok client secrets: {e}")
    
    if not client_key or not client_secret:
        raise ValueError("TikTok client_key and client_secret are required in client secrets file")
    
    # Validate redirect_uri
    if not redirect_uri:
        redirect_uri = DEFAULT_REDIRECT_URI
        if show_status:
            print(f"   ⚠️  No redirect_uri specified, using default: {redirect_uri}")
    
    if show_status:
        print("\n" + "=" * 80)
        print("⚠️  REDIRECT URI CONFIGURATION CHECK")
        print("=" * 80)
        print(f"   Using redirect_uri: '{redirect_uri}'")
        print(f"\n   📋 BEFORE CONTINUING, verify this redirect_uri is configured in TikTok Developer Portal:")
        print(f"   1. Go to: https://developers.tiktok.com/console")
        print(f"   2. Select your app")
        print(f"   3. Go to: Settings → Platform information")
        print(f"   4. Find 'Redirect URI' or 'Callback URL' field")
        print(f"   5. Add EXACTLY this value: {redirect_uri}")
        print(f"   6. Make sure there are NO extra spaces, slashes, or characters")
        print(f"   7. Save the changes")
        print(f"   8. Wait 1-2 minutes for changes to propagate")
        print(f"\n   ⚠️  The redirect_uri MUST match EXACTLY (case-sensitive, no trailing slash)")
        print("=" * 80 + "\n")
    
    # Generate PKCE code verifier and challenge
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    
    # For OAuth flow with PKCE, we need to guide user through browser
    # TikTok scopes can be space-separated or comma-separated
    # Try space-separated first (most common)
    scope_string = ' '.join(TIKTOK_SCOPES)
    
    # Build authorization URL according to TikTok OAuth documentation
    # https://developers.tiktok.com/doc/oauth-user-access-token-management
    auth_params = {
        "client_key": client_key,
        "scope": scope_string,
        "response_type": "code",
        "redirect_uri": redirect_uri,  # Will be URL encoded by urlencode
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    # Use urlencode to properly encode all parameters
    auth_url = f"https://www.tiktok.com/v2/auth/authorize/?{urllib.parse.urlencode(auth_params)}"
    
    if show_status:
        print(f"   ℹ️  Requesting scopes: {scope_string}")
        print(f"   ⚠️  If you get a scope error, verify these scopes are enabled in your TikTok app settings")
    
    if show_status:
        print("   🌐 Opening browser for authentication...")
        print("   📝 Please follow these steps:")
        print("   1. Authorize the app in the browser")
        print("   2. Copy the authorization code from the redirect URL")
        print(f"   (If browser didn't open, visit: {auth_url})")
    
    # Open browser automatically
    try:
        webbrowser.open(auth_url)
    except Exception as e:
        if show_status:
            print(f"   ⚠️  Could not open browser automatically: {e}")
            print(f"   Please open this URL manually: {auth_url}")
    
    auth_code = input("\n   Enter authorization code: ").strip()
    
    # URL decode the authorization code (as per TikTok documentation)
    # The code from the redirect URL may be URL encoded
    try:
        auth_code = urllib.parse.unquote(auth_code)
    except Exception:
        pass  # If decoding fails, use as-is
    
    # Exchange code for token (with PKCE code_verifier)
    # IMPORTANT: redirect_uri must match EXACTLY what was used in authorization request
    # According to TikTok docs: https://developers.tiktok.com/doc/oauth-user-access-token-management
    token_data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": auth_code,  # Should be URL decoded per TikTok docs
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,  # Must match exactly the one in auth URL
        "code_verifier": code_verifier  # Required for desktop apps
    }
    
    if show_status:
        print(f"   🔄 Exchanging code for token...")
        print(f"   ℹ️  Using redirect_uri: {redirect_uri}")
        print(f"   ℹ️  Code (decoded): {auth_code[:20]}...")
    
    # According to TikTok docs, Content-Type should be application/x-www-form-urlencoded
    # Using data= parameter automatically sets this header
    token_response = requests.post(
        TIKTOK_TOKEN_URL,
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data=token_data
    )
    
    if token_response.status_code != 200:
        error_text = token_response.text
        error_msg = f"Failed to get access token (Status {token_response.status_code}): {error_text}"
        
        # Provide helpful error message for redirect_uri errors
        if "redirect_uri" in error_text.lower() or ("redirect" in error_text.lower() and "uri" in error_text.lower()):
            error_msg += (
                f"\n\n❌ REDIRECT_URI ERROR:\n"
                f"   The redirect_uri '{redirect_uri}' doesn't match what's configured in TikTok Developer Portal.\n"
                f"\n   🔧 TROUBLESHOOTING STEPS:\n"
                f"   1. Go to: https://developers.tiktok.com/console\n"
                f"   2. Select your app\n"
                f"   3. Go to: Settings → Platform information\n"
                f"   4. Find 'Redirect URI' or 'Callback URL' field\n"
                f"   5. Check what's currently configured\n"
                f"   6. It must be EXACTLY: {redirect_uri}\n"
                f"      - No trailing slash\n"
                f"      - Case-sensitive\n"
                f"      - No extra spaces\n"
                f"   7. If different, update to: {redirect_uri}\n"
                f"   8. Save and wait 1-2 minutes\n"
                f"   9. Update tiktok_client_secret.json if you changed the redirect_uri\n"
                f"\n   📝 Common mistakes:\n"
                f"   - Using https:// instead of http://\n"
                f"   - Adding trailing slash: http://localhost:8080/\n"
                f"   - Different port number\n"
                f"   - Extra spaces or characters\n"
            )
        
        # Provide helpful error message for scope errors
        if "scope" in error_text.lower():
            error_msg += (
                f"\n\n❌ SCOPE ERROR:\n"
                f"   The requested scopes are not enabled or not valid for your TikTok app.\n"
                f"\n   🔧 TROUBLESHOOTING STEPS:\n"
                f"   1. Go to: https://developers.tiktok.com/console\n"
                f"   2. Select your app\n"
                f"   3. Go to: Settings → Basic Information or Permissions\n"
                f"   4. Enable the following scopes in your app:\n"
                f"      - user.info.basic (Read user's profile info)\n"
                f"      - video.upload (Share content as draft)\n"
                f"      - video.publish (Directly post content)\n"
                f"   5. Save the changes\n"
                f"   6. Wait 1-2 minutes for changes to propagate\n"
                f"   7. Try again\n"
                f"\n   📝 Note: All three scopes must be enabled in your TikTok app settings.\n"
                f"   Go to: Settings → Permissions or Basic Information → Scopes\n"
            )
        
        raise Exception(error_msg)
    
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 3600)
    
    if not access_token:
        raise Exception("No access token in response")
    
    # Save token
    token_save_data = {
        "access_token": access_token,
        "expires_at": time.time() + expires_in,
        "refresh_token": token_data.get("refresh_token"),
        "token_type": token_data.get("token_type", "Bearer")
    }
    
    with open(token_path, "w", encoding="utf-8") as f:
        json.dump(token_save_data, f, indent=2)
    
    if show_status:
        print("   ✓ Authentication successful\n")
    
    return access_token


def upload_and_schedule(
    video_path: Path,
    publish_time: datetime,
    access_token: str,
    video_number: int = 0,
    total_videos: int = 0,
    dry_run: bool = False,
    description: str = "",
    privacy_level: str = "PUBLIC_TO_EVERYONE"
) -> dict:
    """
    Upload a video to TikTok and schedule it for publication.
    
    Args:
        video_path: Path to video file
        publish_time: When to publish the video
        access_token: TikTok API access token
        video_number: Current video number
        total_videos: Total number of videos
        dry_run: If True, don't actually upload
        description: Video description
        privacy_level: Privacy level (PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY)
    
    Returns:
        Dictionary with upload results
    """
    raw_title = video_path.stem
    title, title_warnings = sanitize_title(raw_title)
    
    # Show warnings if any
    if title_warnings:
        for warning in title_warnings:
            print(f"   ⚠️  Title warning for '{raw_title}': {warning}")
    
    file_size = video_path.stat().st_size
    start_time = time.time()
    
    # TikTok has max 10 days scheduling limit
    max_schedule_days = 10
    now = datetime.now(publish_time.tzinfo)
    days_ahead = (publish_time - now).days
    
    if days_ahead > max_schedule_days:
        raise ValueError(f"TikTok only allows scheduling up to {max_schedule_days} days in advance")
    
    if days_ahead < 0:
        raise ValueError("Cannot schedule videos in the past")
    
    # If dry run, just return preview info
    if dry_run:
        return {
            'dry_run': True,
            'title': title,
            'raw_title': raw_title,
            'title_warnings': title_warnings,
            'file_size': file_size,
            'scheduled_time': publish_time,
            'days_ahead': days_ahead
        }
    
    # Step 1: Initialize upload
    init_url = f"{TIKTOK_API_BASE}/post/publish/inbox/video/init/"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8"
    }
    
    chunk_size = 5 * 1024 * 1024  # 5MB chunks
    total_chunks = (file_size // chunk_size) + (1 if file_size % chunk_size > 0 else 0)
    
    init_data = {
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": chunk_size,
            "total_chunk_count": total_chunks
        },
        "post_info": {
            "title": title,
            "description": description,
            "privacy_level": privacy_level,
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 1000
        }
    }
    
    # Add schedule if more than 15 minutes in future
    if days_ahead > 0 or (publish_time - now).total_seconds() > 900:
        init_data["post_info"]["schedule_time"] = int(publish_time.timestamp())
    
    init_response = requests.post(init_url, headers=headers, json=init_data)
    
    if init_response.status_code != 200:
        error_msg = f"Failed to initialize upload: {init_response.text}"
        raise Exception(error_msg)
    
    init_result = init_response.json()
    upload_url = init_result["data"]["upload_url"]
    publish_id = init_result["data"]["publish_id"]
    
    # Step 2: Upload video in chunks
    progress_bar = tqdm(
        total=file_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
        desc=f"📤 [{video_number}/{total_videos}] {title[:40]:<40}",
        ncols=100,
        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
    )
    
    with open(video_path, 'rb') as video_file:
        for chunk_num in range(total_chunks):
            chunk = video_file.read(chunk_size)
            chunk_start = chunk_num * chunk_size
            chunk_end = min(chunk_start + len(chunk) - 1, file_size - 1)
            
            chunk_headers = {
                "Content-Type": "video/mp4",
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {chunk_start}-{chunk_end}/{file_size}"
            }
            
            chunk_response = requests.put(upload_url, headers=chunk_headers, data=chunk)
            
            if chunk_response.status_code not in [200, 201, 204]:
                progress_bar.close()
                raise Exception(f"Failed to upload chunk {chunk_num + 1}/{total_chunks}: {chunk_response.text}")
            
            progress_bar.update(len(chunk))
            
            # Calculate and display speed
            elapsed = time.time() - start_time
            if elapsed > 0:
                uploaded_bytes = chunk_start + len(chunk)
                speed = uploaded_bytes / elapsed
                remaining_bytes = file_size - uploaded_bytes
                eta_seconds = remaining_bytes / speed if speed > 0 else 0
                progress_bar.set_postfix({
                    'speed': format_file_size(speed) + '/s',
                    'eta': format_duration(eta_seconds)
                })
    
    progress_bar.close()
    
    # Step 3: Commit upload
    commit_url = f"{TIKTOK_API_BASE}/post/publish/inbox/video/commit/"
    commit_data = {
        "publish_id": publish_id
    }
    
    commit_response = requests.post(commit_url, headers=headers, json=commit_data)
    
    if commit_response.status_code != 200:
        raise Exception(f"Failed to commit upload: {commit_response.text}")
    
    commit_result = commit_response.json()
    video_id = commit_result.get("data", {}).get("publish_id")
    
    # Calculate upload statistics
    upload_time = time.time() - start_time
    upload_speed = file_size / upload_time if upload_time > 0 else 0
    
    # Print success message
    print(
        f"   ✓ Uploaded: {title[:50]}\n"
        f"     📊 Size: {format_file_size(file_size)} | "
        f"⏱️  Time: {format_duration(upload_time)} | "
        f"🚀 Speed: {format_file_size(upload_speed)}/s\n"
        f"     🆔 TikTok Publish ID: {video_id}\n"
        f"     📅 Scheduled: {publish_time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
    )
    
    # Save to history
    add_upload_to_history(
        filename=video_path.name,
        youtube_id=video_id,  # Reusing field name for TikTok ID
        scheduled_time=publish_time,
        file_size=file_size,
        upload_time=upload_time,
        upload_speed=upload_speed,
        status="success"
    )
    
    # Mark as uploaded in tracking system
    upload_tracker.mark_uploaded(
        filename=video_path.name,
        platform="tiktok",
        video_id=video_id,
        scheduled_time=publish_time
    )
    
    return {
        'upload_time': upload_time,
        'file_size': file_size,
        'upload_speed': upload_speed,
        'tiktok_id': video_id,
        'publish_id': publish_id
    }


def main() -> None:
    """Main function to orchestrate video uploads."""
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
        args.platforms = ['tiktok']
    
    # Create backup
    backup_files()
    
    # Validate and parse timezone
    try:
        timezone = ZoneInfo(args.timezone)
    except Exception as e:
        error_msg = f"Invalid timezone '{args.timezone}'"
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
    
    # Get description from args or config
    description = args.description if args.description else config.get("description", "")
    
    if args.dry_run:
        print("🔍 DRY-RUN MODE: Preview only, no videos will be uploaded\n")
    else:
        print("🚀 Starting TikTok uploads...\n")
    
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
    
    # Find video files (only those not yet uploaded to TikTok)
    print("📁 Scanning for video files...")
    video_extensions = set(config.get("video_extensions", [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"]))
    
    # Get pending videos (not uploaded to TikTok yet)
    videos = upload_tracker.get_pending_videos(CLIPS_FOLDER, args.platforms, video_extensions)
    
    if not videos:
        print(f"   ✓ No pending videos found in: {CLIPS_FOLDER}")
        print(f"   (All videos have already been uploaded to TikTok)")
        return
    
    # Calculate total size
    total_size = sum(v.stat().st_size for v in videos)
    print(f"   ✓ Found {len(videos)} pending video(s) ({format_file_size(total_size)} total)\n")
    
    # Authenticate (skip in dry-run mode)
    access_token = None
    if not args.dry_run:
        try:
            access_token = get_authenticated_token(
                TIKTOK_CLIENT_SECRETS_FILE, 
                TIKTOK_TOKEN_FILE, 
                show_status=True
            )
        except FileNotFoundError as e:
            log_error(str(e), "ERROR", e)
            sys.exit(1)
        except Exception as e:
            log_error(f"Authentication failed: {e}", "ERROR", e)
            sys.exit(1)
    
    # Calculate scheduling
    base_day = start_date.date()
    
    total_videos = len(videos)
    successful_uploads = 0
    failed_uploads = 0
    total_upload_time = 0
    total_uploaded_size = 0
    
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
        # Calculate publish time
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
            privacy_level = config.get("tiktok_privacy_level", "PUBLIC_TO_EVERYONE")
            result = upload_and_schedule(
                video_path,
                publish_dt,
                access_token,
                video_number=idx,
                total_videos=total_videos,
                dry_run=args.dry_run,
                description=description,
                privacy_level=privacy_level
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
            
            # Check if should move to sent (only if uploaded to all requested platforms)
            if upload_tracker.should_move_to_sent(video_path.name, args.platforms):
                upload_tracker.move_to_sent(video_path)
        
        except Exception as e:
            failed_uploads += 1
            error_msg = str(e)
            
            # Log error
            log_error(
                f"Error processing {video_path.name}: {error_msg}",
                "ERROR",
                e
            )
            
            # Mark as failed in tracking
            upload_tracker.mark_uploaded(
                filename=video_path.name,
                platform="tiktok",
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
            
            # Continue processing other videos
            continue
    
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


def parse_arguments(config: dict[str, Any]) -> argparse.Namespace:
    """Parse command-line arguments with defaults from config file."""
    parser = argparse.ArgumentParser(
        description="Upload and schedule videos to TikTok",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
        "--platforms",
        type=str,
        nargs="+",
        default=["tiktok"],
        help="Platforms to upload to. Used for tracking when uploading to multiple platforms. Default: tiktok"
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    main()

