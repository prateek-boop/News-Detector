# 🔧 Data Fixes Applied - Quick Start Guide

## TL;DR - What You Need to Know

Your scraper had **incorrect data** - it was storing **impression counts** (views) instead of **registration counts**. This has been fixed!

### What Changed
- ✅ **New Field**: `impression_count` - Page views/impressions  
- ✅ **New Field**: `registration_count` - Actual registrations
- ✅ **Fixed**: Contact information extraction
- ✅ **New Script**: `update_unstop` to refresh existing data

---

## 🚀 Quick Start - Fix Your Data in 3 Steps

### Step 1: Activate Virtual Environment
```bash
cd /home/sonu/Desktop/unstop_crawler
source .venv/bin/activate
```

### Step 2: Update Your 457 Existing Hackathons
```bash
# This will take ~50-60 minutes for all 457 hackathons
python manage.py update_unstop --all --outdated-only
```

**Or test with just 5 first:**
```bash
python manage.py update_unstop --all --limit 5
```

### Step 3: Export Corrected Data
```bash
python manage.py export_hackathons --format csv --output corrected_data.csv
```

---

## 📊 What's Different Now

### Before (Wrong ❌)
```json
{
  "registered_count": "60,498 Registration",  // Actually impressions!
  "impression_count": null,
  "registration_count": null
}
```

### After (Correct ✅)
```json
{
  "registered_count": "1234",      // For backward compatibility
  "registration_count": "1234",    // Actual registrations
  "impression_count": "60498"      // Page views
}
```

---

## 📝 Usage Examples

### Update All Outdated Hackathons
```bash
python manage.py update_unstop --all --outdated-only
```

### Update Specific Hackathon by ID
```bash
python manage.py update_unstop --id 5
```

### Update Specific Hackathon by URL
```bash
python manage.py update_unstop --url "https://unstop.com/hackathons/example-123"
```

### Update First 10 Hackathons
```bash
python manage.py update_unstop --all --limit 10
```

---

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `FIX_SUMMARY.md` | Complete overview of what was fixed |
| `UPDATE_GUIDE.md` | Detailed guide for update_unstop command |
| `CHANGES.md` | Technical changelog |
| `QUICK_REFERENCE.txt` | Quick command reference |

---

## 🔍 Verify the Fix

Check if a hackathon has been updated:

```bash
python manage.py shell
```

```python
from scraper.models import Hackathon

h = Hackathon.objects.first()
print(f"Name: {h.name}")
print(f"Registrations: {h.registration_count}")  # Should have value after update
print(f"Impressions: {h.impression_count}")      # Should have value after update
```

---

## ⚡ Performance

- **Speed**: ~7-8 seconds per hackathon (includes page load + processing)
- **Total Time**: ~50-60 minutes for 457 hackathons
- **Safe**: Respects server with 2-second delays between requests

---

## 🎯 Future Scrapes

All new scrapes will automatically extract both counts correctly:

```bash
python manage.py scrape_unstop --limit 10
```

The new hackathons will have both `registration_count` and `impression_count` populated from the start.

---

## ❓ Troubleshooting

### "No new data found"
The page structure may have changed or data isn't available. This is logged as a warning.

### ChromeDriver Issues
Make sure Chrome/Chromium is installed:
```bash
which chromium  # Should show /usr/bin/chromium
```

### Update Taking Too Long
Use `--limit` to update in batches:
```bash
python manage.py update_unstop --all --limit 50
```

---

## 🎉 That's It!

Your scraper now correctly extracts:
- ✅ Registration counts (actual participant registrations)
- ✅ Impression counts (page views)
- ✅ Organizer contact information
- ✅ All other hackathon details

Run the update command and you're all set! 🚀
