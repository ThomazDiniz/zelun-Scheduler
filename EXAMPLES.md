# 📚 Usage Examples

This document provides practical examples of using the YouTube Bulk Scheduler script.

## Basic Examples

### Example 1: Default Configuration
Run with all default settings (from `config.json` or built-in defaults):
```bash
python youtube_bulk_scheduler.py
```

### Example 2: Custom Start Date
Schedule videos starting from a specific date:
```bash
python youtube_bulk_scheduler.py --start-date 2025-12-01
```

### Example 3: Different Timezone
Use a different timezone for scheduling:
```bash
python youtube_bulk_scheduler.py --timezone America/New_York
```

### Example 4: Custom Time Slots
Upload videos at specific times each day:
```bash
# One video per day at 10 AM
python youtube_bulk_scheduler.py --hour-slots 10

# Three videos per day
python youtube_bulk_scheduler.py --hour-slots 9 12 18
```

### Example 5: Different Category
Upload videos to a specific category:
```bash
python youtube_bulk_scheduler.py --category-id 10  # Music
```

## Advanced Examples

### Example 6: Dry-Run Preview
Preview what would be uploaded without actually uploading:
```bash
python youtube_bulk_scheduler.py --dry-run
```

This is useful to:
- Check if titles are valid
- See the scheduling plan
- Verify file sizes
- Test before actual upload

### Example 7: Combined Options
Use multiple options together:
```bash
python youtube_bulk_scheduler.py \
  --start-date 2025-12-15 \
  --timezone America/Sao_Paulo \
  --hour-slots 8 12 16 20 \
  --category-id 20
```

## Configuration Examples

### Weekly Scheduling
Edit `config.json`:
```json
{
  "schedule_mode": "weekly",
  "schedule_day": "monday",
  "schedule_hour": 10,
  "default_timezone": "America/Sao_Paulo"
}
```

This will schedule one video every Monday at 10:00 AM.

### Playlist Support
Edit `config.json`:
```json
{
  "playlist_id": "PLxxxxx",
  "default_timezone": "America/Sao_Paulo"
}
```

Or create a new playlist:
```json
{
  "create_playlist": true,
  "playlist_title": "My Upload Series",
  "default_timezone": "America/Sao_Paulo"
}
```

### Custom Start Date in Config
Edit `config.json`:
```json
{
  "default_start_date": "2025-12-01",
  "default_timezone": "America/Sao_Paulo"
}
```

## File Organization Examples

### Subtitles
Place subtitle files with the same name as videos:
```
clips/
  video1.mp4
  video1.srt        # English subtitles
  video1.pt-BR.srt  # Portuguese subtitles
  video2.mp4
  video2.vtt        # WebVTT format
```

### Thumbnails
Place thumbnail files with the same name as videos:
```
clips/
  video1.mp4
  video1.png        # Thumbnail for video1
  video2.mp4
  video2.png        # Thumbnail for video2
```

## Common Use Cases

### Use Case 1: Daily Upload Schedule
**Goal**: Upload 2 videos per day for a week

**Setup**:
1. Place 14 videos in `clips/` folder
2. Run: `python youtube_bulk_scheduler.py --hour-slots 8 18`

**Result**: 
- Day 1: Videos 1-2 at 8:00 and 18:00
- Day 2: Videos 3-4 at 8:00 and 18:00
- ... and so on

### Use Case 2: Weekly Series
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

### Use Case 3: Preview Before Upload
**Goal**: Check scheduling before uploading

**Setup**:
1. Place videos in `clips/` folder
2. Run: `python youtube_bulk_scheduler.py --dry-run`

**Result**: See preview of what would be uploaded without actually uploading

### Use Case 4: Videos with Subtitles and Thumbnails
**Goal**: Upload videos with accessibility features

**Setup**:
1. Organize files:
   ```
   clips/
     video1.mp4
     video1.srt
     video1.png
     video2.mp4
     video2.srt
     video2.png
   ```
2. Run: `python youtube_bulk_scheduler.py`

**Result**: Videos uploaded with subtitles and custom thumbnails

## Troubleshooting Examples

### Problem: Title Too Long
**Solution**: The script automatically truncates titles over 100 characters and shows a warning.

### Problem: Invalid Characters in Title
**Solution**: The script automatically removes invalid characters (like `<` and `>`) and shows a warning.

### Problem: Concurrent Execution
**Solution**: The script uses a lock file to prevent multiple instances. If you see an error about another instance running, wait for it to finish.

### Problem: Authentication Issues
**Solution**: 
1. Delete `token.json`
2. Run the script again to re-authenticate
3. Check that `client_secret.json` is valid

## Best Practices

1. **Always use `--dry-run` first** to preview your uploads
2. **Check title warnings** in dry-run output
3. **Use config.json** for frequently used settings
4. **Keep backups** - the script automatically backs up config and history
5. **Monitor error_log.txt** for any issues
6. **Check upload_history.json** to track what was uploaded

