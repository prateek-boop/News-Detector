# Unstop & Devfolio Crawler - Quick Reference

## 🚀 Quick Start

```bash
# View comprehensive help
python manage.py guide

# Get help for any specific command
python manage.py <command> --help
```

## 📋 Common Commands

### Get All URLs
```bash
# Unstop (hackathons + competitions)
python manage.py get_all_urls

# Devfolio (all statuses)
python manage.py get_devfolio_urls --status all
```

### Scrape Data
```bash
# Unstop hackathons
python manage.py scrape_unstop --from-file hackathon_urls.txt

# Unstop competitions  
python manage.py scrape_competitions --from-file hackathon_urls.txt

# Devfolio hackathons
python manage.py scrape_devfolio --from-file devfolio_all_urls.txt
```

### Update Data
```bash
# Update specific URL
python manage.py update_unstop --url <URL>

# Update all outdated records
python manage.py update_unstop --outdated-only

# Update contacts only
python manage.py update_unstop --update-contacts
```

### Export Data
```bash
# Export to JSON/CSV
python manage.py export_hackathons
python manage.py export_competitions
python manage.py export_devfolio

# Export to Supabase (sorted alphabetically)
python manage.py export_to_supabase
python manage.py export_to_supabase --table Unstop
python manage.py export_to_supabase --table Devfolio
```

## 📊 Data Fields

### Unstop (Hackathons & Competitions)
- Name, URL, Organizer
- Registration count (actual registrations)
- Impression count (page views)  
- About content, Important dates
- Organizer contact (Unstop support excluded)
- Official website, Prizes

### Devfolio
- Name, URL, Organizer, Status
- Participants count, Projects count
- About content, Dates (start/end)
- Location, Mode (online/offline/hybrid)
- Prizes, Themes, Contact info
- Official website

## 🔄 Typical Workflow

1. **Initial Setup**
   ```bash
   python manage.py get_all_urls
   python manage.py get_devfolio_urls --status all
   ```

2. **Scrape Everything**
   ```bash
   python manage.py scrape_unstop --from-file hackathon_urls.txt
   python manage.py scrape_competitions --from-file hackathon_urls.txt  
   python manage.py scrape_devfolio --from-file devfolio_all_urls.txt
   ```

3. **Export**
   ```bash
   python manage.py export_hackathons
   python manage.py export_competitions
   python manage.py export_devfolio
   python manage.py export_to_supabase
   ```

4. **Periodic Updates**
   ```bash
   python manage.py update_unstop --outdated-only
   ```

## 💡 Tips

- Use `--limit N` to test with small batches
- Use `--skip-existing` to avoid re-scraping
- Use `--force-rescrape` to update all records
- Unstop support number (+91-9311777388) is automatically excluded
- Data is sorted alphabetically when exporting to Supabase

## 📁 Output Files

- `hackathon_urls.txt` - All Unstop URLs
- `devfolio_all_urls.txt` - All Devfolio URLs
- `json/hackathons_export.json` - Unstop hackathons
- `json/competitions_export.json` - Unstop competitions
- `json/devfolio.json` - Devfolio hackathons
- `csv/` - CSV exports
- `db.sqlite3` - Local SQLite database
