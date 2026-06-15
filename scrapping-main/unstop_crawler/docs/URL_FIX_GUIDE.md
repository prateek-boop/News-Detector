# Devfolio Data Fixes

## Issues Fixed

### 1. URL Format Issue
The scraper was saving incorrect URL format:
- ❌ **OLD (Wrong)**: `https://devfolio.co/hackathons/ethindia`
- ✅ **NEW (Correct)**: `https://ethindia.devfolio.co/overview`

### 2. Organizer Name Issue
The scraper was saving city names as organizer:
- ❌ **OLD (Wrong)**: Organizer: "Bengaluru" (this is the city!)
- ✅ **NEW (Correct)**: Organizer: "Ethindia" (actual hackathon name)

## What Was Fixed

### Files Updated:
1. **`scraper/management/commands/scrape_devfolio.py`**
   - Line 210: Fixed URL generation in API scraping
   - Line 236: Fixed URL in save_hackathon_from_api()
   - Line 239-246: Fixed organizer extraction logic (no longer uses city as fallback)

2. **`scraper/management/commands/get_devfolio_urls.py`**
   - Line 125: Fixed URL format when extracting from API

### New Utility Scripts:
- **`fix_devfolio_urls.py`** - Converts existing database URLs to correct format
- **`fix_devfolio_organizers.py`** - Fixes organizer names that are actually city names

## How to Fix Existing Data

### Step 1: Fix URLs in Database
```bash
python fix_devfolio_urls.py
```

This will:
- Scan all Devfolio hackathons in database
- Convert old URL format to new format
- Show summary of changes

### Step 2: Fix Organizer Names in Database
```bash
python fix_devfolio_organizers.py
```

This will:
- Scan all Devfolio hackathons
- Identify organizers that are actually city names
- Replace with proper hackathon names
- Show summary of changes

### Step 3: Verify the Fixes
```bash
# Export to JSON to verify both URLs and organizers
python manage.py export_devfolio --format json

# Check the data in devfolio_export.json
cat devfolio_export.json | jq '.[] | {name, url, organizer, location}' | head -50
```

### Step 4: Update Supabase (if already exported)
```bash
# Update existing records in Supabase with correct data
python manage.py export_to_supabase -d devfolio --update-existing
```

## Future Scraping

All new scrapes will automatically use the correct URL format:

```bash
# Scrape new hackathons (will use correct format)
python manage.py scrape_devfolio --status all

# Get URLs (will generate correct format)
python manage.py get_devfolio_urls --status all --output urls.txt
```

## URL Format Pattern

**Template:**
```
https://{slug}.devfolio.co/overview
```

**Examples:**
- ETHIndia: `https://ethindia.devfolio.co/overview`
- HackIndia: `https://hackindia.devfolio.co/overview`
- CodeJam: `https://codejam.devfolio.co/overview`

## Verification

To verify URLs are correct:

```bash
# Check database
python manage.py shell
>>> from scraper.models import DevfolioHackathon
>>> hackathon = DevfolioHackathon.objects.first()
>>> print(hackathon.url)
# Should print: https://something.devfolio.co/overview

# Check a sample URL works
curl -I https://ethindia.devfolio.co/overview
# Should return: HTTP/2 200
```

## Summary

✅ **Fixed Files**: 2 Python command files  
✅ **New Scripts**: 2 utility scripts (URL fixer + Organizer fixer)  
✅ **URL Pattern**: `https://{slug}.devfolio.co/overview`  
✅ **Organizer Logic**: Uses hackathon name instead of city  
✅ **Backward Compatible**: Old data can be fixed with utility scripts

## Example: Before vs After

### Before (Wrong):
```json
{
  "name": "Ethindia",
  "url": "https://devfolio.co/hackathons/ethindia",
  "organizer": "Bengaluru",
  "location": "Bengaluru, Karnataka, India"
}
```

### After (Correct):
```json
{
  "name": "Ethindia", 
  "url": "https://ethindia.devfolio.co/overview",
  "organizer": "Ethindia",
  "location": "Bengaluru, Karnataka, India"
}
```

## Related Documentation

- `DEVFOLIO_FEATURE.md` - Complete Devfolio scraping guide
- `SUPABASE_EXPORT_GUIDE.md` - Export to Supabase guide
