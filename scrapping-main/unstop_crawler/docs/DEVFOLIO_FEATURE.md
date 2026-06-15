# Devfolio Scraper Feature

Complete Devfolio hackathon scraping functionality with export capabilities.

## ✅ Status: Ready to Use (--from-file mode recommended)

##Overview

The Devfolio scraper extracts comprehensive hackathon data from devfolio.co, supporting:
- Open, past, and upcoming hackathons  
- Full hackathon details including prizes, themes, and contact info
- JSON and CSV export formats
- File-based scraping for manual URL lists

## Commands

### scrape_devfolio - Scrape Devfolio Hackathons

```bash
# Recommended: Scrape from file
python manage.py scrape_devfolio --from-file devfolio_urls.txt

# Scrape specific status
python manage.py scrape_devfolio --status open --limit 10

# Scrape all statuses
python manage.py scrape_devfolio --status all --headless
```

### export_devfolio - Export Data

```bash
# Export to JSON
python manage.py export_devfolio --format json

# Export to CSV
python manage.py export_devfolio --format csv

# Export filtered by status
python manage.py export_devfolio --status open --format csv
```

## Quick Start

Since Devfolio uses heavy JavaScript rendering, use the file-based approach:

**Step 1**: Create a file with Devfolio URLs (one per line):
```
devfolio_urls.txt:
https://devfolio.co/hackathons/hackathon-1
https://devfolio.co/hackathons/hackathon-2
https://devfolio.co/hackathons/hackathon-3
```

**Step 2**: Scrape from file:
```bash
python manage.py scrape_devfolio --from-file devfolio_urls.txt
```

**Step 3**: Export data:
```bash
python manage.py export_devfolio --format csv --output devfolio_data.csv
```

## Extracted Data Fields

- Basic: name, organizer, status, URL
- Stats: participants_count, projects_count
- Dates: start_date, end_date, important_dates
- Location: location, mode (online/offline/hybrid)
- Content: about_content, prizes, themes
- Contact: organizer_contact, official_website

## Important Note

⚠️ **Devfolio uses heavy client-side rendering**. The `--from-file` method is most reliable.

For automated scraping, the tool is ready but may need adjustments based on Devfolio's current page structure.

## See Also

- Full documentation in code docstrings
- Use `--help` flag for detailed options
- Similar to Unstop scraper but optimized for Devfolio
