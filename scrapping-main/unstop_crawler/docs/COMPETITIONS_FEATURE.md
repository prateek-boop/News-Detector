# 🎯 Competitions Scraping Feature

## Overview
The Unstop scraper now supports scraping **Competitions** in addition to Hackathons! 
Both use the same robust extraction logic and features.

---

## 🆕 What's New

### New Model: Competition
Similar to Hackathon but with an additional `prizes` field to capture prize information.

**Fields:**
- name
- url (unique)
- organizer
- registration_count
- impression_count
- registered_count (legacy)
- about_content
- organizer_contact
- important_dates
- official_website
- **prizes** (NEW - specific to competitions)
- scraped_at
- updated_at

---

## 📝 New Commands

### 1. scrape_competitions
Scrapes competitions from Unstop (similar to scrape_unstop for hackathons).

```bash
# Scrape 10 competitions
python manage.py scrape_competitions --limit 10

# Skip already scraped
python manage.py scrape_competitions --skip-existing

# Start from page 5
python manage.py scrape_competitions --start-page 5

# Force rescrape all
python manage.py scrape_competitions --force-rescrape
```

**Options:**
- `--use-selenium` - Use Selenium browser (slower but more reliable)
- `--headless` - Run browser in background
- `--limit N` - Scrape only N competitions
- `--skip-existing` - Skip already scraped (default: True)
- `--force-rescrape` - Rescrape everything
- `--skip-pages N` - Skip first N pages
- `--skip-competitions N` - Skip first N competitions
- `--start-page N` - Start from specific page

### 2. export_competitions
Export competitions to JSON or CSV.

```bash
# Export to CSV sorted by name
python manage.py export_competitions --format csv --sort name

# Export to JSON sorted by registrations
python manage.py export_competitions --format json --sort registrations

# Custom output filename
python manage.py export_competitions --output my_competitions.csv
```

**Sort Options:**
- `name` - Alphabetically by name
- `organizer` - Group by organizer
- `registrations` - Highest registration count first
- `date` - Most recent first (default)

---

## 🔄 Updated Commands - Enhanced Help

All commands now have comprehensive help text:

```bash
python manage.py scrape_unstop --help
python manage.py scrape_competitions --help
python manage.py update_unstop --help
python manage.py export_hackathons --help
python manage.py export_competitions --help
python manage.py export_to_supabase --help
```

Each help message now includes:
- ✓ Detailed description
- ✓ What data is extracted
- ✓ Usage examples
- ✓ All available options

---

## 💾 Database Changes

**Migration:** `0004_competition.py`
- Created Competition model
- Already applied to database

**Admin Panel:**
- Competitions now visible in Django admin
- Same interface as Hackathons

---

## 📊 Usage Examples

### Complete Workflow

```bash
# 1. Scrape competitions
python manage.py scrape_competitions --limit 50

# 2. Check what you got
python manage.py shell
>>> from scraper.models import Competition
>>> Competition.objects.count()
50

# 3. Export to CSV
python manage.py export_competitions --format csv --sort date

# 4. Export to JSON with custom name
python manage.py export_competitions --format json --output latest_comps.json
```

### Compare Hackathons vs Competitions

```bash
# Get counts
python manage.py shell
>>> from scraper.models import Hackathon, Competition
>>> print(f"Hackathons: {Hackathon.objects.count()}")
>>> print(f"Competitions: {Competition.objects.count()}")

# Export both
python manage.py export_hackathons --format csv --output hackathons.csv
python manage.py export_competitions --format csv --output competitions.csv
```

---

## 🎨 Features Inherited from Hackathons

Competitions scraper includes ALL the improvements made to hackathons:

✅ **Smart Extraction**
- Registration vs Impression counts properly separated
- Unstop support numbers filtered out
- Multiple extraction patterns for different page types

✅ **Contact Information**
- Targets app-dates-and-contacts component
- Filters out generic text
- Excludes Unstop's own contact details

✅ **Important Dates**
- Extracts rounds, stages, deadlines
- Handles multiple date formats
- Captures timeline information

✅ **Duplicate Detection**
- Skips already scraped competitions
- Stops after 20 consecutive duplicates
- Much faster scraping

✅ **Error Handling**
- Graceful failure recovery
- Detailed error messages
- Progress tracking

---

## 🚀 Quick Reference

| Task | Command |
|------|---------|
| Scrape 10 competitions | `python manage.py scrape_competitions --limit 10` |
| Export to CSV | `python manage.py export_competitions --format csv` |
| View in admin | Start server, go to /admin/scraper/competition/ |
| Count scraped | `Competition.objects.count()` in shell |
| Check latest | `Competition.objects.first()` in shell |

---

## 📈 Current Status

```
Hackathons scraped: 457
Competitions scraped: 3 (just tested)
Total opportunities: 460+
```

---

## 🎯 Recommendation

**When to use Hackathons:**
- Traditional coding hackathons
- CTF competitions
- Programming challenges

**When to use Competitions:**
- Business competitions
- Case competitions  
- Design challenges
- General contests
- Campus ambassador programs

Both share the same robust scraping engine and can be used interchangeably!

---

## 🔧 Technical Notes

- Both use Unstop's public API for listing pages
- Individual pages scraped with Selenium for JavaScript content
- Same extraction methods for counts, contacts, dates
- Separate database tables for clean organization
- Can be exported independently or together
