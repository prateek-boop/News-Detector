# Unstop Crawler - Complete Command Guide

Quick reference for all scraping, export, and management commands.

## Quick Help

```bash
# Show all available commands
python manage.py unstop_help

# Get detailed help for any command
python manage.py <command> --help
```

---

## 📥 SCRAPING COMMANDS

### 1. Scrape Unstop Hackathons
```bash
python manage.py scrape_unstop [OPTIONS]
```

**Examples:**
```bash
# Scrape 50 hackathons
python manage.py scrape_unstop --limit 50

# Scrape all new hackathons
python manage.py scrape_unstop

# Scrape from URL file
python manage.py scrape_unstop --from-file hackathon_urls.txt

# Force rescrape existing
python manage.py scrape_unstop --force-rescrape --limit 20
```

**Options:**
- `--limit N` - Limit to N hackathons
- `--skip-existing` - Skip already scraped (default)
- `--force-rescrape` - Rescrape everything
- `--from-file FILE` - Scrape URLs from file
- `--use-selenium` - Use Selenium (slower but reliable)

---

### 2. Scrape Unstop Competitions
```bash
python manage.py scrape_competitions [OPTIONS]
```

**Examples:**
```bash
# Scrape 30 competitions
python manage.py scrape_competitions --limit 30

# Scrape from URL file
python manage.py scrape_competitions --from-file competition_urls.txt
```

**Options:**
- Same as `scrape_unstop`

---

### 3. Scrape Devfolio Hackathons
```bash
python manage.py scrape_devfolio [OPTIONS]
```

**Examples:**
```bash
# Scrape all open hackathons
python manage.py scrape_devfolio --status open

# Scrape all statuses
python manage.py scrape_devfolio --status all

# Scrape past hackathons (limited)
python manage.py scrape_devfolio --status past --limit 50

# Force rescrape
python manage.py scrape_devfolio --status all --force-rescrape
```

**Options:**
- `--status {open,past,upcoming,all}` - Status to scrape (default: all)
- `--limit N` - Limit per status
- `--skip-existing` - Skip already scraped
- `--force-rescrape` - Rescrape everything
- `--from-file FILE` - Scrape URLs from file (for detailed data)

---

### 4. Get All URLs
```bash
python manage.py get_all_urls [OPTIONS]
```

Extract all hackathon and competition URLs from Unstop.

**Examples:**
```bash
# Get all URLs and save to file
python manage.py get_all_urls --output unstop_urls.txt

# Get only hackathon URLs
python manage.py get_all_urls --type hackathons --output hackathon_urls.txt

# Get only competition URLs
python manage.py get_all_urls --type competitions --output competition_urls.txt

# Get all (both types)
python manage.py get_all_urls --type all --output all_urls.txt
```

**Options:**
- `--type {hackathons,competitions,all}` - Type of URLs to extract
- `--output FILE` - Output file (default: unstop_urls.txt)
- `--headless` - Run in headless mode

---

## 🔄 UPDATE COMMANDS

### Update Unstop Data
```bash
python manage.py update_unstop [OPTIONS]
```

Update existing hackathon data with latest information.

**Examples:**
```bash
# Update specific hackathon by URL
python manage.py update_unstop --url https://unstop.com/hackathons/example-123

# Update by database ID
python manage.py update_unstop --id 42

# Update all hackathons
python manage.py update_unstop --all

# Update only outdated (missing contact/counts)
python manage.py update_unstop --all --outdated-only

# Update first 20 outdated hackathons
python manage.py update_unstop --all --outdated-only --limit 20
```

**Options:**
- `--all` - Update all hackathons
- `--url URL` - Update specific URL
- `--id ID` - Update by database ID
- `--outdated-only` - Only update missing data
- `--limit N` - Limit number to update

**What Gets Updated:**
- Registration count
- Impression count
- About content
- Organizer contact
- Important dates
- Official website

---

## 📤 EXPORT COMMANDS

### 1. Export Hackathons
```bash
python manage.py export_hackathons [OPTIONS]
```

Export to CSV and JSON.

**Examples:**
```bash
# Export all
python manage.py export_hackathons

# Export only recent
python manage.py export_hackathons --limit 100

# Export to custom location
python manage.py export_hackathons --output custom_dir/
```

**Output Files:**
- `csv/hackathons.csv` - CSV format
- `json/hackathons.json` - JSON format

---

### 2. Export Competitions
```bash
python manage.py export_competitions [OPTIONS]
```

Same as export_hackathons but for competitions.

**Output Files:**
- `csv/competitions.csv`
- `json/competitions.json`

---

### 3. Export Devfolio
```bash
python manage.py export_devfolio [OPTIONS]
```

Export Devfolio hackathons to CSV/JSON.

**Output Files:**
- `devfolio.csv`
- `devfolio.json`

---

### 4. Export to Supabase
```bash
python manage.py export_to_supabase [OPTIONS]
```

Export data to Supabase PostgreSQL database.

**Examples:**
```bash
# Export only new records (default, recommended)
python manage.py export_to_supabase

# Export with sorting
python manage.py export_to_supabase --sort name
python manage.py export_to_supabase --sort registrations

# Update existing records too
python manage.py export_to_supabase --update-existing

# Clear and re-export all
python manage.py export_to_supabase --clear
```

**Options:**
- `--sort {name,date,organizer,registrations}` - Sort order
- `--new-only` - Only new records (default)
- `--update-existing` - Update existing records
- `--clear` - Clear all data first

---

## 💾 DATABASE COMMANDS

### Setup Supabase Security
```bash
python manage.py setup_supabase_security
```

Setup Row Level Security policies for Supabase.

---

### Test Supabase Access
```bash
python manage.py test_supabase_access
```

Test connection to Supabase database.

---

## 🎯 COMMON WORKFLOWS

### Full Scraping Workflow
```bash
# 1. Get all URLs
python manage.py get_all_urls --type all --output urls.txt

# 2. Scrape hackathons
python manage.py scrape_unstop --from-file urls.txt

# 3. Scrape competitions
python manage.py scrape_competitions --from-file urls.txt

# 4. Scrape Devfolio
python manage.py scrape_devfolio --status all

# 5. Export to Supabase
python manage.py export_to_supabase --sort name
```

### Update Workflow
```bash
# 1. Update outdated data
python manage.py update_unstop --all --outdated-only --limit 50

# 2. Export updated data
python manage.py export_to_supabase --update-existing
```

### Export Workflow
```bash
# Export all formats
python manage.py export_hackathons
python manage.py export_competitions
python manage.py export_devfolio
python manage.py export_to_supabase
```

---

## 📊 DATA FIELDS

### Hackathon Fields
- name
- url
- organizer
- registered_count (legacy field)
- registration_count (actual registrations)
- impression_count (views)
- about_content
- organizer_contact
- important_dates
- official_website
- scraped_at
- updated_at

### Competition Fields
Same as Hackathon plus:
- prizes

### Devfolio Fields
- name
- url
- organizer
- status (open/past/upcoming)
- participants_count
- projects_count
- about_content
- start_date
- end_date
- location
- mode (online/offline/hybrid)
- prizes
- themes
- organizer_contact
- important_dates
- official_website

---

## ⚙️ Configuration

### Browser Configuration
Edit `browser_config.py` for:
- Chrome profile path
- User agent
- Browser binary location

### Environment Variables
Create `.env` file:
```
SUPABASE_PASSWORD=your_password_here
```

---

## 🐛 Troubleshooting

### Scraping Issues
```bash
# Use Selenium mode if requests fail
python manage.py scrape_unstop --use-selenium

# Update outdated contact details
python manage.py update_unstop --all --outdated-only
```

### Export Issues
```bash
# Test Supabase connection first
python manage.py test_supabase_access

# Clear and re-export if needed
python manage.py export_to_supabase --clear
```

### Database Issues
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Check database
python manage.py dbshell
```

---

## 📝 Notes

- **Headless Mode**: Most commands support headless browser operation
- **Rate Limiting**: Built-in delays to avoid overwhelming servers
- **Resume Support**: `--skip-existing` allows resuming interrupted scrapes
- **Data Validation**: Automatic cleaning of Unstop support numbers (+91-9311777388)
- **Progress Tracking**: Real-time progress indicators for long operations

---

For more details on any command:
```bash
python manage.py <command> --help
```
