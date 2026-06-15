# Unstop Crawler - Recent Changes

## Summary of Changes

### 1. Database Schema Updates
**New Fields Added:**
- `impression_count` - Stores the number of views/impressions (was incorrectly stored in registered_count)
- `registration_count` - Stores the actual number of registrations

**Migration:**
- Created migration `0003_hackathon_impression_count_and_more.py`
- Already applied to database

### 2. Fixed Data Extraction Issues

#### Registration vs Impression Count
**Problem:** The scraper was extracting impression count instead of registration count.

**Solution:** 
- Modified `extract_registered_count()` method to properly distinguish between:
  - **Registrations**: Actual participant registrations
  - **Impressions**: Page views/impressions
- Both values are now extracted separately and stored in their respective fields

#### Contact Information Extraction
**Problem:** Contact details were not being extracted correctly from Unstop pages.

**Solution:**
- Improved `extract_organizer_contact()` to target the specific `app-dates-and-contacts` section
- Better filtering to exclude Unstop's own contact info
- Enhanced pattern matching for emails, phone numbers, and contact details

### 3. New Update Script: `update_unstop.py`

**Purpose:** Update existing hackathon data without rescraping everything from scratch.

**Features:**
- Update all hackathons or specific ones by ID/URL
- Filter to only update outdated entries (missing impression/registration counts)
- Limit the number of hackathons to update
- Properly extracts and updates all fields

**Usage Examples:**
```bash
# Update all hackathons with missing data
python manage.py update_unstop --all --outdated-only

# Update specific hackathon
python manage.py update_unstop --id 5

# Update first 10 hackathons
python manage.py update_unstop --all --limit 10
```

### 4. Updated Export Scripts

**Modified Files:**
- `export_hackathons.py` - Now exports impression_count and registration_count
- `export_to_supabase.py` - Supabase table schema updated with new fields

**Export Format Changes:**
- JSON exports now include `impression_count` and `registration_count`
- CSV exports have separate columns for both counts
- Legacy `registered_count` field maintained for backward compatibility

### 5. Code Improvements

**In `scrape_unstop.py`:**
- Updated `extract_registered_count()` to return both registration and impression counts
- Modified `scrape_hackathon_page()` to handle the new tuple return value
- Updated `save_hackathon_from_api()` to save both counts
- Updated `scrape_hackathon_selenium()` for consistency

## Files Modified

1. `scraper/models.py` - Added new fields
2. `scraper/management/commands/scrape_unstop.py` - Fixed extraction logic
3. `scraper/management/commands/update_unstop.py` - **NEW** update script
4. `scraper/management/commands/export_hackathons.py` - Updated exports
5. `scraper/management/commands/export_to_supabase.py` - Updated Supabase schema

## Migration Steps

If you're updating an existing installation:

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Run migrations
python manage.py migrate

# 3. Update existing data (optional)
python manage.py update_unstop --all --outdated-only

# 4. Export updated data (optional)
python manage.py export_hackathons --format csv --output updated_hackathons.csv
```

## What's Fixed

✅ **Impression vs Registration Count** - Now properly separated and labeled
✅ **Contact Information** - Improved extraction targeting correct sections  
✅ **Data Updates** - Can now update existing hackathons without full rescrape
✅ **Export Formats** - All exports include the new fields
✅ **Supabase Schema** - Updated to match new database structure

## Backward Compatibility

- The `registered_count` field is retained and mirrors `registration_count`
- Old exports will still work, but won't have the new fields
- Existing data remains intact; new fields are nullable

## Testing

To verify the changes work:

```bash
# Test the update script on a single hackathon
python manage.py update_unstop --id 1

# Check the data
python manage.py shell
>>> from scraper.models import Hackathon
>>> h = Hackathon.objects.first()
>>> print(f"Registration: {h.registration_count}, Impression: {h.impression_count}")
```

## Notes

- The scraper now uses Selenium for individual page scraping to ensure JavaScript content loads
- There's a 5-second wait for page load and 2-second delay between requests
- Contact extraction prioritizes the `app-dates-and-contacts` component
- Both counts are extracted using regex patterns looking for "X Registrations" and "X Impressions"
