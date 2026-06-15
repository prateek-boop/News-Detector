# Unstop Crawler - Command Reference

Complete guide to all available management commands.

## Table of Contents

1. [Scraping Commands](#scraping-commands)
2. [Export Commands](#export-commands)
3. [Update Commands](#update-commands)
4. [Utility Commands](#utility-commands)

---

## Scraping Commands

### `scrape_unstop` - Scrape Hackathons

Scrape hackathon data from Unstop with comprehensive extraction.

**Basic Usage:**
```bash
# Scrape first 10 hackathons
python manage.py scrape_unstop --limit 10

# Scrape all new hackathons (skips existing)
python manage.py scrape_unstop

# Rescrape everything
python manage.py scrape_unstop --force-rescrape
```

**Advanced Usage:**
```bash
# Scrape from URL file
python manage.py scrape_unstop --from-file hackathon_urls.txt

# Start from specific page
python manage.py scrape_unstop --start-page 5 --limit 50

# Skip first 100 hackathons
python manage.py scrape_unstop --skip-hackathons 100

# Use Selenium mode (slower but more reliable)
python manage.py scrape_unstop --use-selenium --limit 20
```

**Options:**
- `--limit N` - Scrape only N hackathons
- `--skip-existing` - Skip already scraped (default: True)
- `--force-rescrape` - Rescrape even if in database
- `--start-page N` - Start from page N
- `--skip-pages N` - Skip first N pages
- `--skip-hackathons N` - Skip first N hackathons
- `--from-file FILE` - Read URLs from file
- `--use-selenium` - Use browser-based scraping
- `--headless` - Run browser in headless mode

---

### `scrape_competitions` - Scrape Competitions

Scrape competition data from Unstop with prizes and detailed info.

**Basic Usage:**
```bash
# Scrape first 10 competitions
python manage.py scrape_competitions --limit 10

# Scrape all new competitions
python manage.py scrape_competitions

# Rescrape everything
python manage.py scrape_competitions --force-rescrape
```

**Advanced Usage:**
```bash
# Scrape from URL file
python manage.py scrape_competitions --from-file competition_urls.txt

# Start from specific page
python manage.py scrape_competitions --start-page 3 --limit 30
```

**Options:**
- `--limit N` - Scrape only N competitions
- `--skip-existing` - Skip already scraped (default: True)
- `--force-rescrape` - Rescrape even if in database
- `--start-page N` - Start from page N
- `--skip-competitions N` - Skip first N competitions
- `--from-file FILE` - Read URLs from file

**Note:** Competitions take ~19 seconds each due to contact extraction wait times.

---

## Export Commands

### `export_hackathons` - Export Hackathon Data

Export scraped hackathons to JSON or CSV format.

**Basic Usage:**
```bash
# Export to JSON (default)
python manage.py export_hackathons

# Export to CSV
python manage.py export_hackathons --format csv
```

**With Sorting:**
```bash
# Sort by name
python manage.py export_hackathons --format csv --sort name

# Sort by registration count (highest first)
python manage.py export_hackathons --format json --sort registrations

# Sort by date (most recent first)
python manage.py export_hackathons --sort date
```

**Custom Output:**
```bash
# Specify output file
python manage.py export_hackathons --output my_hackathons.json

# Export to specific directory
python manage.py export_hackathons --output exports/data.csv
```

**Sorting Options:**
- `name` - Alphabetical by hackathon name
- `date` - By scraped date (most recent first)
- `organizer` - Alphabetical by organizer
- `registrations` - By registration count (highest first)

---

### `export_competitions` - Export Competition Data

Export scraped competitions to JSON or CSV format.

**Basic Usage:**
```bash
# Export to JSON (default)
python manage.py export_competitions

# Export to CSV
python manage.py export_competitions --format csv
```

**With Sorting:**
```bash
# Sort by name
python manage.py export_competitions --format csv --sort name

# Sort by registration count
python manage.py export_competitions --format json --sort registrations
```

**Custom Output:**
```bash
# Specify output file
python manage.py export_competitions --output competitions.json
```

---

## Update Commands

### `update_unstop` - Update Hackathon Data

Update existing hackathons with latest data without full rescrape.

**Update by URL:**
```bash
python manage.py update_unstop --url https://unstop.com/hackathons/example-123
```

**Update by ID:**
```bash
python manage.py update_unstop --id 42
```

**Bulk Update:**
```bash
# Update all hackathons
python manage.py update_unstop --all

# Update only outdated (missing contact/counts)
python manage.py update_unstop --all --outdated-only

# Update first 20 outdated
python manage.py update_unstop --all --outdated-only --limit 20
```

**What Gets Updated:**
- Registration count and impression count
- About content
- Organizer contact information
- Important dates
- Official website

---

## Utility Commands

### `get_all_urls` - Get All URLs

Fetch all unique hackathon/competition URLs from Unstop (no duplicates).

**Basic Usage:**
```bash
# Get all hackathon URLs
python manage.py get_all_urls --type hackathons

# Get all competition URLs
python manage.py get_all_urls --type competitions

# Get both
python manage.py get_all_urls --type both
```

**Save to File:**
```bash
# Save hackathon URLs
python manage.py get_all_urls --type hackathons --output hackathon_urls.txt

# Save competition URLs
python manage.py get_all_urls --type competitions --output competition_urls.txt
```

**With Statistics:**
```bash
# Show statistics about URLs
python manage.py get_all_urls --type hackathons --show-stats --output urls.txt
```

**Output:**
- URLs are printed to stdout or saved to file
- One URL per line
- No duplicates
- Can fetch 2000+ URLs

---

## Common Workflows

### Workflow 1: Complete Hackathon Scrape

```bash
# Step 1: Get all URLs
python manage.py get_all_urls --type hackathons --output hackathon_urls.txt

# Step 2: Scrape from file
python manage.py scrape_unstop --from-file hackathon_urls.txt

# Step 3: Export data
python manage.py export_hackathons --format csv --sort registrations --output hackathons.csv
```

### Workflow 2: Complete Competition Scrape

```bash
# Step 1: Get all URLs
python manage.py get_all_urls --type competitions --output competition_urls.txt

# Step 2: Scrape from file (takes time due to contact extraction)
python manage.py scrape_competitions --from-file competition_urls.txt

# Step 3: Export data
python manage.py export_competitions --format json --output competitions.json
```

### Workflow 3: Update Outdated Data

```bash
# Update hackathons with missing contact info
python manage.py update_unstop --all --outdated-only

# Export updated data
python manage.py export_hackathons --format csv
```

### Workflow 4: Quick Sample

```bash
# Get sample of latest hackathons
python manage.py scrape_unstop --limit 50

# Export them
python manage.py export_hackathons --format csv --sort date --output latest_50.csv
```

---

## Getting Help

```bash
# Main Django help
python manage.py --help

# Command-specific help
python manage.py scrape_unstop --help
python manage.py scrape_competitions --help
python manage.py export_hackathons --help
python manage.py export_competitions --help
python manage.py update_unstop --help
python manage.py get_all_urls --help
```

---

## Tips & Best Practices

1. **Start Small**: Always test with `--limit 10` first
2. **Use URL Files**: For large scrapes, use `get_all_urls` first then scrape from file
3. **Monitor Progress**: Commands show progress indicators
4. **Skip Existing**: Default behavior skips already scraped items (efficient)
5. **Export Regularly**: Export data periodically as backup
6. **Update Strategically**: Use `--outdated-only` to update only what's needed
7. **Competition Timing**: Competitions take ~19s each due to contact extraction

---

## Troubleshooting

**Problem**: Scraping is slow  
**Solution**: Use `--limit` to test, or use API mode (default) instead of Selenium

**Problem**: Missing contact info  
**Solution**: Run `python manage.py update_unstop --all --outdated-only`

**Problem**: Duplicate data  
**Solution**: `get_all_urls` automatically removes duplicates

**Problem**: Browser errors  
**Solution**: Make sure Chromium/Chrome is installed and browser_config.py is correct

---

## Data Fields Reference

### Hackathon Fields
- `id` - Database ID
- `name` - Hackathon name
- `url` - Unstop URL
- `organizer` - Organizing institution
- `registration_count` - Number of registrations
- `impression_count` - Number of impressions/views
- `about_content` - Full description
- `organizer_contact` - Contact emails/phones
- `important_dates` - Deadlines and timeline
- `official_website` - External website
- `scraped_at` - When first scraped
- `updated_at` - Last update time

### Competition Fields
Same as hackathons, plus:
- `prizes` - Prize details and amounts

