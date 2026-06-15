# Devpost Scraper - Quick Start Guide

## ✅ What's Fixed

1. **URL Fetching**: Now fetches 8,325+ URLs (was 165) using direct API calls
2. **Data Extraction**: Optimized to extract only essential fields:
   - ✅ ID (auto-generated)
   - ✅ Name
   - ✅ Organizer (extracted from page title "presented by X")
   - ✅ Participants count (accurate numbers)
   - ✅ Contact details (emails and phones)
   - ✅ Sponsors (when available)

3. **Database Updates**: Added `--update-database` flag to refresh existing records

## 🚀 Quick Start (3 Steps)

### Step 1: Get All Devpost URLs
```bash
source .venv/bin/activate
python manage.py get_devpost_urls_api
```
**Output**: `devpost_all_urls.txt` with 8,325+ hackathon URLs

### Step 2: Scrape Hackathon Data
```bash
# Scrape all hackathons (headless mode recommended)
python manage.py scrape_devpost --from-file devpost_all_urls.txt --headless

# Or scrape first 10 to test
python manage.py scrape_devpost --from-file devpost_all_urls.txt --limit 10 --headless

# Scrape single hackathon
python manage.py scrape_devpost --url https://hackthetrack.devpost.com --headless
```

### Step 3: Export to Supabase or JSON
```bash
# Export to Supabase
python manage.py export_devpost --format supabase

# Export to JSON
python manage.py export_devpost --format json
```

## 📊 Example Output

```json
{
    "id": 3,
    "name": "Hackthetrack",
    "url": "https://hackthetrack.devpost.com",
    "organizer": "Toyota GR",
    "participants_count": "544",
    "organizer_contact": "Email: trd.hackathon@toyota.com",
    "sponsors": ""
}
```

## 🔧 Advanced Usage

### Update Existing Records
If you need to re-scrape to fix missing data:
```bash
python manage.py scrape_devpost --url https://example.devpost.com --headless --update-database
```

### Skip Already Scraped
Default behavior - skips URLs already in database:
```bash
python manage.py scrape_devpost --from-file devpost_all_urls.txt --skip-existing --headless
```

## 📝 All Available Commands

Run `python manage.py --help` to see all commands. Key Devpost commands:

- `get_devpost_urls_api` - Fetch all hackathon URLs (FAST, uses API)
- `scrape_devpost` - Scrape hackathon data (headless mode recommended)
- `export_devpost` - Export to JSON/CSV/Supabase

For detailed help on any command:
```bash
python manage.py <command> --help
```

## 🎯 Data Fields Extracted

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Auto-generated database ID | `3` |
| `name` | Hackathon name | `Hackthetrack` |
| `url` | Devpost URL | `https://hackthetrack.devpost.com` |
| `organizer` | Organizing company/institution | `Toyota GR` |
| `participants_count` | Number of participants | `544` |
| `organizer_contact` | Email addresses and phone numbers | `Email: contact@example.com` |
| `sponsors` | Sponsor names (comma-separated) | `Google, Microsoft` |

## ⚡ Performance

- **URL Fetching**: ~20 minutes for 8,325+ URLs
- **Scraping**: ~5-10 seconds per hackathon
- **Total Time**: ~12-18 hours for all 8,325 hackathons
- **Headless Mode**: Recommended for faster performance

## 💡 Tips

1. **Always use `--headless` flag** for faster scraping
2. **Use `--limit` to test** before running full scrape
3. **Monitor progress** - script shows progress for each hackathon
4. **Export frequently** - export data after scraping batches
5. **Resume from failures** - script skips existing URLs by default

## 📊 Success Metrics

- ✅ **8,325 hackathon URLs** collected (50x improvement)
- ✅ **Accurate participant counts** extracted
- ✅ **Organizer names** from page titles
- ✅ **Contact details** including emails and phones
- ✅ **Sponsor information** when available
- ✅ **Database updates** supported

## 🎉 You're Ready!

Run the 3-step process above to scrape all Devpost hackathons!
