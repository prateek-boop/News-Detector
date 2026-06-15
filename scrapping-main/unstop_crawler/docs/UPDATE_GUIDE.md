# Unstop Crawler - Update Guide

## Overview
The update script allows you to refresh existing hackathon data in the database with the latest information from Unstop.

## New Features

### Database Changes
- **`impression_count`**: Stores the number of impressions/views
- **`registration_count`**: Stores the actual number of registrations (fixed from incorrect data)
- **`registered_count`**: Kept for backward compatibility, mirrors registration_count

## Usage

### Update All Hackathons
```bash
python manage.py update_unstop --all
```

### Update Only Outdated Entries
Update only hackathons missing impression_count or registration_count:
```bash
python manage.py update_unstop --all --outdated-only
```

### Update Limited Number
Update only first N hackathons:
```bash
python manage.py update_unstop --all --limit 10
```

### Update Specific Hackathon by URL
```bash
python manage.py update_unstop --url "https://unstop.com/hackathons/example-hackathon-123"
```

### Update Specific Hackathon by ID
```bash
python manage.py update_unstop --id 5
```

## What Gets Updated

The script will update the following fields:
- ✅ **registration_count** - Actual registration count (fixed)
- ✅ **impression_count** - Number of views/impressions (new)
- ✅ **about_content** - Description and details
- ✅ **organizer_contact** - Contact information (fixed extraction)
- ✅ **important_dates** - Timeline and deadlines
- ✅ **official_website** - External website link

## Examples

### Fix all outdated data
```bash
# This will update all hackathons that have missing impression or registration counts
python manage.py update_unstop --all --outdated-only
```

### Update top 20 hackathons
```bash
python manage.py update_unstop --all --limit 20
```

### Update a specific hackathon
```bash
python manage.py update_unstop --id 1
```

## Notes

- The script uses Selenium to properly render JavaScript content
- It waits 5 seconds for each page to load completely
- There's a 2-second delay between updates to be respectful to the server
- Contact information extraction has been improved to target the correct section
- Registration vs Impression counts are now properly separated

## Migration

After pulling the latest changes, run:
```bash
python manage.py migrate
```

This will add the new `impression_count` and `registration_count` fields to your database.

## Troubleshooting

### "No new data found"
This means the scraper couldn't extract the data. The page structure might have changed or the data isn't available.

### ChromeDriver issues
Make sure Chrome/Chromium is installed and webdriver-manager can download the driver:
```bash
pip install webdriver-manager
```

### Virtual environment
Always activate your virtual environment first:
```bash
source .venv/bin/activate
```
