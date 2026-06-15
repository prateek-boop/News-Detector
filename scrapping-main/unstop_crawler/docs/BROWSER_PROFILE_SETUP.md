# 🌐 Browser Profile Configuration

## Overview

The scraper now uses your **existing Chromium Profile 2** for all web scraping operations. This means:

✅ Your browser cookies are used  
✅ Login sessions are preserved  
✅ Browser extensions are loaded (if needed)  
✅ Settings and preferences are maintained  

## Configuration File

All browser settings are now in **`browser_config.py`**:

```python
USER_DATA_DIR = "/home/sonu/.config/chromium"
PROFILE_NAME = "Profile 2"
BROWSER_BINARY = "/usr/bin/chromium"
```

## How to Change Profile

### Option 1: Edit browser_config.py

```python
# To use Default profile instead
PROFILE_NAME = "Default"

# To use Profile 1
PROFILE_NAME = "Profile 1"

# To use Chrome instead of Chromium
USER_DATA_DIR = "/home/sonu/.config/google-chrome"
BROWSER_BINARY = "/usr/bin/google-chrome"
```

### Option 2: Check Available Profiles

```bash
ls -la ~/.config/chromium/ | grep Profile
```

Output will show:
- Default
- Profile 1
- Profile 2
- System Profile

## Benefits of Using Your Profile

1. **Cookies & Sessions**: If you're logged into Unstop, the scraper uses your session
2. **No Bot Detection**: Uses your real browser fingerprint
3. **Faster Scraping**: Reuses cached data and connections
4. **Extensions**: Any installed extensions work (ad blockers, etc.)

## Important Notes

⚠️ **Do NOT run Chromium manually while scraping**  
- Chromium can only use one profile at a time
- Close Chromium before running the scraper
- Or use a different profile in the config

⚠️ **Headless Mode**  
- The scraper runs in headless mode (no visible window)
- This is faster and doesn't interrupt your work
- The browser still uses all profile data

## Testing

```bash
# Test with your profile
python manage.py scrape_unstop --limit 1

# Check if profile is being used
# You should see better extraction if logged in
python manage.py scrape_unstop --limit 5
```

## Troubleshooting

### Error: "Profile is in use"
- Close all Chromium windows
- Run: `pkill chromium`
- Try again

### Error: "Cannot find profile"
- Check profile exists: `ls ~/.config/chromium/`
- Update PROFILE_NAME in browser_config.py

### Error: "Browser binary not found"
- Find browser: `which chromium chromium-browser google-chrome`
- Update BROWSER_BINARY in browser_config.py

## Current Configuration

✅ Using: **Chromium**  
✅ Profile: **Profile 2**  
✅ Location: **/home/sonu/.config/chromium/Profile 2**  
✅ Mode: **Headless** (background)  

All working perfectly! 🎉
