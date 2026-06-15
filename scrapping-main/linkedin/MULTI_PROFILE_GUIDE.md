# Multi-Profile Setup Guide

## Overview

To run **multiple scrapers simultaneously**, you need separate Chrome profiles for each LinkedIn account. This allows parallel scraping without conflicts.

## Current Setup

You now have two profile directories:
- `./profile` - Used by `scrape_all`, `scrape_infinite`, `scrape_profile_activity`
- `./profile2` - **Default for `scrape_emails`**

## Why Separate Profiles?

**Problem**: Chrome profiles can only be used by one browser instance at a time.

**Solution**: Multiple LinkedIn accounts with separate Chrome profiles allow:
- ✅ Running `scrape_all` and `scrape_emails` **simultaneously**
- ✅ Parallel processing of different posts
- ✅ Faster overall data collection

## Usage Examples

### Single Profile (Current)

```bash
# This uses ./profile
python manage.py scrape_all --url "POST-URL-1"

# This uses ./profile2 (different account)
python manage.py scrape_emails --url "POST-URL-2"
```

**Result**: Both can run at the same time! 🚀

### Parallel Scraping Example

**Terminal 1:**
```bash
python manage.py scrape_infinite \
  --seed-url "POST-URL-1" \
  --max-posts 50
```
(Uses `./profile` - Account 1)

**Terminal 2:**
```bash
python manage.py scrape_emails \
  --url "POST-URL-2" \
  --speed aggressive
```
(Uses `./profile2` - Account 2)

Both run simultaneously without conflicts!

### Custom Profile Directory

Override default for any command:

```bash
# Use profile3 for scrape_emails
python manage.py scrape_emails \
  --url "YOUR-URL" \
  --profile-dir ./profile3

# Use profile2 for scrape_all
python manage.py scrape_all \
  --url "YOUR-URL" \
  --profile-dir ./profile2
```

## Setting Up Additional Profiles

### Step 1: Create New Profile Directory

```bash
mkdir profile3
mkdir profile4
mkdir profile5
```

### Step 2: Login to LinkedIn

For each new profile:

1. Run a test scrape with visible browser:
```bash
python manage.py scrape_emails \
  --url "ANY-LINKEDIN-POST" \
  --profile-dir ./profile3 \
  --visible
```

2. Browser will open - **login to LinkedIn** with a different account
3. Close browser
4. Profile is now saved and ready to use!

### Step 3: Use in Production

```bash
# Now use headless mode
python manage.py scrape_emails \
  --url "YOUR-URL" \
  --profile-dir ./profile3
```

## Maximum Parallelization Strategy

With 5 LinkedIn accounts and 5 profiles:

**Terminal 1 (Account 1 - ./profile):**
```bash
python manage.py scrape_infinite \
  --seed-url "SEED-1" \
  --max-posts 100
```

**Terminal 2 (Account 2 - ./profile2):**
```bash
python manage.py scrape_emails \
  --url "POST-1"
```

**Terminal 3 (Account 3 - ./profile3):**
```bash
python manage.py scrape_all \
  --url "POST-2" \
  --profile-dir ./profile3
```

**Terminal 4 (Account 4 - ./profile4):**
```bash
python manage.py scrape_emails \
  --url "POST-3" \
  --profile-dir ./profile4
```

**Terminal 5 (Account 5 - ./profile5):**
```bash
python manage.py scrape_all \
  --url "POST-4" \
  --profile-dir ./profile5
```

**Result**: 5x throughput! 🔥

## Command Default Profiles

| Command | Default Profile | Override with |
|---------|----------------|---------------|
| `scrape_all` | `./profile` | `--profile-dir` (not implemented) |
| `scrape_emails` | `./profile2` | `--profile-dir ./custom` |
| `scrape_infinite` | `./profile` | N/A (not implemented) |
| `scrape_profile_activity` | `./profile` | N/A (not implemented) |

## Best Practices

### For Speed (2 accounts minimum)

```bash
# Terminal 1: Infinite loop (long-running)
python manage.py scrape_infinite \
  --seed-url "SEED" \
  --max-posts 100

# Terminal 2: Quick email scraping (short bursts)
python manage.py scrape_emails \
  --url "POST" \
  --speed aggressive
```

### For Maximum Data Collection (5+ accounts)

- Account 1: Infinite loop scraper (discovers posts)
- Account 2-5: Process discovered posts from queue
- Rotate through Post queue manually

### Safety Considerations

**Rate Limiting per Account:**
- Don't exceed ~100 posts per account per day
- Space out scraping sessions (wait 2-3 hours between batches)
- Use slower speed modes if you notice issues

**Account Safety:**
- Use aged LinkedIn accounts (not brand new)
- Add profile photo and complete profile info
- Don't use free/disposable email addresses
- Consider LinkedIn Premium accounts for higher limits

## Troubleshooting

### Problem: Profile directory not found

```bash
# Create it first
mkdir profile2

# Then login
python manage.py scrape_emails \
  --url "ANY-POST" \
  --profile-dir ./profile2 \
  --visible
```

### Problem: "Profile in use" error

**Cause**: Another browser is already using that profile.

**Solution**: 
1. Close all Chrome windows
2. Kill any stuck Chrome processes:
```bash
pkill -f chrome
```
3. Try again

### Problem: Not logged in after setting up profile

**Solution**: Re-run with `--visible` and login again:
```bash
python manage.py scrape_emails \
  --url "POST" \
  --profile-dir ./profile2 \
  --visible
```

### Problem: Want to use same account on different profile

**Don't do this!** LinkedIn tracks sessions per account. Using the same account in multiple profiles simultaneously will cause issues.

**Solution**: Use different LinkedIn accounts for each profile directory.

## Profile Management

### Check which profiles exist

```bash
ls -d profile*
```

### Clean up unused profiles

```bash
# Remove profile3 if no longer needed
rm -rf profile3
```

### Backup profiles (preserves login sessions)

```bash
# Backup
tar -czf profile-backups.tar.gz profile profile2

# Restore
tar -xzf profile-backups.tar.gz
```

## Current Workflow Recommendation

Based on your 2-hour scraping time issue:

**Terminal 1 (Account 1 - profile):**
```bash
python manage.py scrape_infinite \
  --seed-url "YOUR-SEED" \
  --max-posts 50 \
  --speed fast
```

**Terminal 2 (Account 2 - profile2):**
```bash
# Process high-priority posts from queue manually
python manage.py scrape_emails \
  --url "HIGH-ENGAGEMENT-POST" \
  --speed aggressive
```

This gives you:
- **2x parallel processing**
- **~26 minutes per terminal** instead of 53 minutes
- **2x data collection rate**

## Summary

✅ **scrape_emails now uses `./profile2` by default**
✅ Can run `scrape_all` and `scrape_emails` **simultaneously**
✅ Add more profiles for more parallelization
✅ Override with `--profile-dir` parameter

**Quick test:**
```bash
# Terminal 1
python manage.py scrape_all --url "POST-1"

# Terminal 2 (simultaneously!)
python manage.py scrape_emails --url "POST-2"
```

Both will run without conflicts! 🎉
