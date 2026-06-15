# Google Dork Crawler

A Django-based web crawler for Google dorking with **SeleniumBase UC mode** (undetected-chromedriver) for superior anti-bot detection bypass.

## Features

- ✅ **SeleniumBase UC Mode** - Uses undetected-chromedriver for better stealth
- ✅ Uses your existing Chromium profile to maintain cookies and session
- ✅ Advanced anti-bot detection measures (UC mode, random delays, human-like scrolling)
- ✅ Stores all dork queries and results in SQLite database via Django ORM
- ✅ Crawls from page 0 to N (configurable)
- ✅ **Headless mode support** for background operation
- ✅ **Export to JSON** with pretty printing
- ✅ **Import from JSON** for bulk dork queries
- ✅ Admin interface to manage dork queries and view results
- ✅ Avoids duplicate URLs
- ✅ Tracks when each query was last crawled

## Installation

Dependencies:
- Django 5.2.8
- **SeleniumBase 4.44.12** (includes undetected-chromedriver)
- Python 3.13+

Already installed in the virtual environment.

## Setup

1. **Run migrations:**
```bash
source .venv/bin/activate
python manage.py makemigrations
python manage.py migrate
```

2. **Create superuser for admin access:**
```bash
python manage.py createsuperuser
```

## Usage

### Command Line Crawling

**Crawl with headless mode (recommended for automation):**
```bash
python manage.py crawl_dorks --query "site:example.com filetype:pdf" --pages 5 --headless
```

**Crawl without headless (for debugging):**
```bash
python manage.py crawl_dorks --query "site:example.com filetype:pdf" --pages 5
```

**Crawl all active dork queries:**
```bash
python manage.py crawl_dorks --all --pages 10 --headless
```

### Export/Import

**Export all data:**
```bash
python manage.py export_json --output results.json --pretty
```

**Export specific query:**
```bash
python manage.py export_json --query "site:example.com" --output specific.json --pretty
```

**Import dork queries:**
```bash
python manage.py import_json example_import.json
```

### Using Django Admin

1. **Start the development server:**
```bash
python manage.py runserver
```

2. **Access admin panel:**
- Go to http://127.0.0.1:8000/admin
- Login with your superuser credentials

3. **Add dork queries:**
- Navigate to "Dork queries"
- Click "Add dork query"
- Enter your dork query and optional description
- Click "Save"

4. **View crawled links:**
- Navigate to "Crawled links" to see all results
- Filter by dork query, page number, or date

### Python API

```python
from crawler.models import DorkQuery
from crawler.crawler_engine import GoogleDorkCrawler

# Create a dork query
dork = DorkQuery.objects.create(
    query='site:github.com "password"',
    description='GitHub password mentions'
)

# Crawl it (headless mode)
crawler = GoogleDorkCrawler(headless=True)
try:
    results = crawler.search_google(dork, max_pages=10)
    print(f"Found {len(results)} new links")
finally:
    crawler.close()
```

## Anti-Bot Detection Features

The crawler uses **SeleniumBase in UC (Undetected-Chromedriver) mode** with additional features:

1. **UC Mode** - Automatically patches detection points
2. **Uses your Chromium profile** - Maintains your cookies, history, and fingerprint
3. **Random delays** - 2-5 seconds between actions, 5-10 seconds between pages
4. **Human-like scrolling** - Scrolls slowly with random intervals
5. **Headless mode support** - Run in background without GUI
6. **CDP bypass** - Content security policy disabled

## Database Models

### DorkQuery
- `query` - The Google dork query string
- `description` - Optional description
- `is_active` - Whether to include in bulk crawls
- `last_crawled` - Timestamp of last crawl
- `created_at` - When the query was added

### CrawledLink
- `dork_query` - Foreign key to DorkQuery
- `url` - The discovered URL
- `title` - Page title from search results
- `snippet` - Text snippet from search results
- `page_number` - Which page it was found on
- `position` - Position on that page
- `found_at` - When it was discovered

## Example Dork Queries

See `example_dorks.txt` for common Google dork patterns.
See `example_import.json` for JSON import format.

## Important Notes

⚠️ **Rate Limiting**: Google will detect and block excessive automated searches. Use responsibly:
- Start with 2-3 pages max
- Wait 30+ seconds between queries
- Don't crawl too many queries at once
- Use headless mode for better performance
- Consider rotating profiles or IPs for heavy use

⚠️ **Legal Compliance**: Only use for legitimate security research and authorized testing.

## Troubleshooting

**CAPTCHA detected:**
- Increase delays between requests
- Reduce number of pages per crawl
- Try non-headless mode first
- Wait before retrying (15-30 minutes)

**No results found:**
- Check if Google changed their HTML structure
- Verify your Chromium profile path is correct
- Ensure Chrome/Chromium is installed
- Try non-headless mode to see what's happening

**Profile in use:**
- Close all Chromium windows using Profile 3
- Or specify a different profile path
- Consider creating a dedicated profile for crawling

## Why SeleniumBase?

SeleniumBase's UC mode provides superior bot detection bypass compared to regular Selenium:
- Automatically patches Chrome DevTools Protocol detection
- Removes automation indicators from navigator object
- Better handling of Google's bot detection mechanisms
- Built-in stealth features that would require manual configuration in Selenium
- Regular updates to stay ahead of detection methods

## Performance Tips

- Use `--headless` for faster operation without GUI overhead
- Set `--pages` to 2-3 for quick scans
- Use `--all` with caution - adds delays between queries
- Export results regularly to avoid data loss
- Monitor Google for CAPTCHA warnings
