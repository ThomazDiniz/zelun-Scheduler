# 📋 Configuration Examples

This document shows configuration examples for `config.json` for different scenarios and regions.

## 🇧🇷 Brazil (Default)

```json
{
  "default_timezone": "America/Sao_Paulo",
  "default_hour_slots": [8, 18],
  "default_category_id": "20",
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
  "privacy_status": "private"
}
```

**Characteristics:**
- Timezone: GMT-3 (Brazil)
- Time slots: 8:00 and 18:00 (morning and afternoon)

---

## 🇺🇸 United States - East Coast

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

---

## 🇺🇸 United States - West Coast

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

---

## 🇬🇧 United Kingdom

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

---

## 🇯🇵 Japan

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

---

## 📺 Multiple Videos Per Day

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

---

## 🎮 Specific Category (Music)

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

---

## 🔓 Public Videos

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

---

## 📅 Custom Start Date

If you want to schedule videos starting from a specific date instead of today:

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

**Example:** With `"default_start_date": "2025-12-01"` and `"default_hour_slots": [8, 18]`:
- Video 1: December 1st at 8:00
- Video 2: December 1st at 18:00
- Video 3: December 2nd at 8:00
- Video 4: December 2nd at 18:00
- And so on...

---

## 📆 Weekly Scheduling

If you want to schedule videos weekly (e.g., every Monday at 12:00):

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

**Example:** With the configuration above (`"schedule_day": "monday"`, `"schedule_hour": 12`), if today is Wednesday and you have 5 videos:
- Video 1: Next Monday at 12:00
- Video 2: Monday of the following week at 12:00
- Video 3: Monday of the week after that at 12:00
- Video 4: Monday of the next week at 12:00
- Video 5: Monday of the following week at 12:00

---

## 📅 Custom Start Date with Weekly Scheduling

If you want to schedule videos weekly starting from a specific date:

```json
{
  "default_timezone": "America/Sao_Paulo",
  "default_category_id": "20",
  "video_extensions": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm"],
  "privacy_status": "private",
  "schedule_mode": "weekly",
  "schedule_day": "wednesday",
  "schedule_hour": 14,
  "default_start_date": "2025-12-01"
}
```

**How it works:**
- The script will find the first occurrence of the target day (`"wednesday"`) from the `default_start_date` (`2025-12-01`)
- If December 1st, 2025 is a Monday, it will find the next Wednesday (December 3rd)
- Each subsequent video will be scheduled for consecutive weeks on the same day

**Example:** With the configuration above, if you have 3 videos:
- Video 1: First Wednesday at 14:00 (from start_date)
- Video 2: Wednesday of the following week at 14:00
- Video 3: Wednesday of the week after that at 14:00

---

## 📝 How to Apply

1. Choose the example that best fits your situation
2. Copy the JSON content
3. Paste into `config.json` (replacing current content)
4. Adjust values as needed
5. Run the script normally

**Note:** You can always override any configuration using command-line arguments.
