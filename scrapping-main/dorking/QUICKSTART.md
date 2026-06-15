# Google Dork Crawler - Quick Reference

## 🚀 Quick Start

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Create superuser (if not done)
python manage.py createsuperuser

# 3. Import example dork queries
python manage.py import_json example_import.json

# 4. Start crawling
python manage.py crawl_dorks --query "site:github.com python" --pages 3

# 5. Export results
python manage.py export_json --output results.json --pretty

# 6. Start admin server
python manage.py runserver
```

## 📋 All Commands

### Crawling
```bash
# Crawl specific query (5 pages)
python manage.py crawl_dorks --query "site:example.com filetype:pdf" --pages 5

# Crawl all active queries (10 pages each)
python manage.py crawl_dorks --all --pages 10
```

### Export/Import
```bash
# Export all data with pretty formatting
python manage.py export_json --output all_data.json --pretty

# Export specific query
python manage.py export_json --query "site:example.com" --output specific.json

# Import dork queries
python manage.py import_json example_import.json
python manage.py import_json my_dorks.json
```

### Django Admin
```bash
# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# Access at: http://127.0.0.1:8000/admin
```

## 📁 Project Structure

```
dorking/
├── crawler/                      # Main app
│   ├── models.py                 # DorkQuery & CrawledLink models
│   ├── admin.py                  # Admin interface config
│   ├── crawler_engine.py         # Selenium crawler with anti-bot
│   └── management/commands/
│       ├── crawl_dorks.py        # Crawling command
│       ├── export_json.py        # Export command
│       └── import_json.py        # Import command
├── dork_crawler/                 # Django project settings
├── example_dorks.txt             # Example dork queries
├── example_import.json           # JSON import example
├── setup.sh                      # Quick setup script
├── README.md                     # Full documentation
└── db.sqlite3                    # Database (created after migrations)
```

## 🎯 JSON Export Format

```json
{
  "dork_queries": [
    {
      "query": "site:example.com filetype:pdf",
      "description": "PDF files on example.com",
      "is_active": true,
      "last_crawled": "2025-11-10T21:56:57.000Z",
      "created_at": "2025-11-10T20:00:00.000Z",
      "links": [
        {
          "url": "https://example.com/file.pdf",
          "title": "Example PDF",
          "snippet": "Description...",
          "page_number": 1,
          "position": 1,
          "found_at": "2025-11-10T21:56:57.000Z"
        }
      ],
      "link_count": 1
    }
  ],
  "total_queries": 1,
  "total_links": 1
}
```

## 🛡️ Anti-Bot Features

✅ Uses your Chromium Profile 3 (cookies, session, fingerprint)
✅ Disables automation detection flags
✅ Random delays (2-10 seconds)
✅ Human-like scrolling
✅ Random user agents
✅ CDP commands to hide webdriver
✅ Detects CAPTCHA and stops gracefully

## ⚠️ Important Tips

1. **Rate Limiting**: Google WILL detect bots. Use responsibly:
   - Start with 2-3 pages max
   - Wait 30+ seconds between queries
   - Don't run too many queries at once

2. **Profile Path**: Default is `/home/sonu/.config/chromium/Profile 3`
   - Close all Chromium windows before crawling
   - Or use a different profile

3. **CAPTCHA**: If detected:
   - Stop crawling immediately
   - Wait 15-30 minutes
   - Reduce pages per query
   - Increase delays

## 🔧 Python API Usage

```python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dork_crawler.settings')
django.setup()

from crawler.models import DorkQuery
from crawler.crawler_engine import GoogleDorkCrawler

# Create query
dork = DorkQuery.objects.create(
    query='site:github.com "api_key"',
    description='GitHub API keys'
)

# Crawl
crawler = GoogleDorkCrawler()
try:
    results = crawler.search_google(dork, max_pages=5)
    print(f"Found {len(results)} new links")
    
    # Access results
    for link in results:
        print(f"{link.url} - {link.title}")
finally:
    crawler.close()
```

## 📊 Database Queries

```python
# Get all links for a query
dork = DorkQuery.objects.get(query="site:example.com")
links = dork.links.all()

# Get links from specific page
page_1_links = CrawledLink.objects.filter(dork_query=dork, page_number=1)

# Get all queries crawled today
from django.utils import timezone
from datetime import timedelta
today = timezone.now() - timedelta(days=1)
recent = DorkQuery.objects.filter(last_crawled__gte=today)

# Export to list
urls = list(dork.links.values_list('url', flat=True))
```
