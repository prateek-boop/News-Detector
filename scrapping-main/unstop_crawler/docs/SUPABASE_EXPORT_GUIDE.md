# Supabase Export Feature - Multi-Destination Support

## Overview

The Unstop Crawler now supports exporting data to Supabase with **two destinations**:
- **Unstop**: Exports to `Unstop` table
- **Devfolio**: Exports to `devfolio` table

## Quick Start

### 1. Create the Devfolio Table Schema

First, create the Devfolio table in Supabase:

```bash
python create_devfolio_supabase_schema.py
```

This will:
- Create the `devfolio` table with proper schema
- Add indexes for better performance
- Add documentation/comments to columns
- Verify the schema structure

### 2. Export Data to Supabase

**Export Unstop data (default):**
```bash
python manage.py export_to_supabase
# or explicitly:
python manage.py export_to_supabase -d unstop
```

**Export Devfolio data:**
```bash
python manage.py export_to_supabase -d devfolio
```

## Command Usage

### Basic Syntax
```bash
python manage.py export_to_supabase [OPTIONS]
```

### Options

| Option | Short | Values | Default | Description |
|--------|-------|--------|---------|-------------|
| `--destination` | `-d` | `unstop`, `devfolio` | `unstop` | Target table to export to |
| `--new-only` | - | flag | `True` | Only export new records |
| `--update-existing` | - | flag | `False` | Update existing records too |
| `--clear` | - | flag | `False` | Clear all data before export |
| `--sort` | - | `name`, `date`, `organizer`, `registrations`, `participants` | `name` | Sort order |

## Examples

### Unstop Exports

```bash
# Export only new Unstop records (default behavior)
python manage.py export_to_supabase -d unstop

# Export and update existing Unstop records
python manage.py export_to_supabase -d unstop --update-existing

# Clear and re-export all Unstop data
python manage.py export_to_supabase -d unstop --clear

# Export sorted by registrations
python manage.py export_to_supabase -d unstop --sort registrations
```

### Devfolio Exports

```bash
# Export only new Devfolio records
python manage.py export_to_supabase -d devfolio

# Export and update existing Devfolio records
python manage.py export_to_supabase -d devfolio --update-existing

# Clear and re-export all Devfolio data
python manage.py export_to_supabase -d devfolio --clear

# Export sorted by participants count
python manage.py export_to_supabase -d devfolio --sort participants

# Export sorted by name
python manage.py export_to_supabase -d devfolio --sort name
```

## Schema Details

### Unstop Table Schema

```sql
CREATE TABLE public.unstop (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  url VARCHAR(500) UNIQUE NOT NULL,
  organizer TEXT,
  registered_count VARCHAR(100),     -- Legacy field
  registration_count VARCHAR(100),   -- Actual registrations
  impression_count VARCHAR(100),     -- Page views
  about_content TEXT,
  organizer_contact TEXT,
  important_dates TEXT,
  official_website TEXT,
  scraped_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

### Devfolio Table Schema

```sql
CREATE TABLE public.devfolio (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  url VARCHAR(500) UNIQUE NOT NULL,
  organizer TEXT,
  status VARCHAR(50),                     -- open, past, upcoming
  participants_count VARCHAR(100),
  projects_count VARCHAR(100),
  about_content TEXT,
  start_date TIMESTAMP WITH TIME ZONE,
  end_date TIMESTAMP WITH TIME ZONE,
  location TEXT,
  organizer_contact TEXT,
  important_dates TEXT,
  official_website TEXT,
  scraped_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);
```

### Key Differences

**Devfolio Schema Excludes:**
- `prizes` field (not stored)
- `themes` field (not stored)
- `mode` field (not stored)

**Devfolio Schema Includes:**
- `status` (open/past/upcoming)
- `start_date` and `end_date` (with timezone)
- `participants_count` and `projects_count`

## Workflow Examples

### First Time Setup

```bash
# 1. Create Devfolio schema
python create_devfolio_supabase_schema.py

# 2. Export both datasets
python manage.py export_to_supabase -d unstop
python manage.py export_to_supabase -d devfolio
```

### Regular Updates

```bash
# Update Unstop data (incremental)
python manage.py export_to_supabase -d unstop

# Update Devfolio data (incremental)
python manage.py export_to_supabase -d devfolio
```

### Full Refresh

```bash
# Clear and re-export Unstop
python manage.py export_to_supabase -d unstop --clear

# Clear and re-export Devfolio
python manage.py export_to_supabase -d devfolio --clear
```

## Export Modes Explained

### 1. New Only (Default)
- Fastest mode
- Only exports records not already in Supabase
- Prevents duplicates
- Recommended for regular updates

```bash
python manage.py export_to_supabase -d devfolio
```

### 2. Update Existing
- Updates existing records
- Adds new records
- Slower but keeps data in sync
- Use when source data has changed

```bash
python manage.py export_to_supabase -d devfolio --update-existing
```

### 3. Clear and Re-export
- Deletes all data first
- Then exports everything
- Fresh start
- Use for major schema changes

```bash
python manage.py export_to_supabase -d devfolio --clear
```

## Sorting Options

### For Unstop (`-d unstop`)
- `--sort name` - Alphabetical by hackathon name
- `--sort date` - By scraped date (most recent first)
- `--sort organizer` - Alphabetical by organizer
- `--sort registrations` - By registration count (highest first)

### For Devfolio (`-d devfolio`)
- `--sort name` - Alphabetical by hackathon name
- `--sort date` - By scraped date (most recent first)
- `--sort organizer` - Alphabetical by organizer
- `--sort participants` - By participants count (highest first)

## Progress Indicators

The export command shows:
- ✅ Connection status
- 📋 Table selection
- 🔍 Existing records check
- 📊 Total records found
- ⏳ Export progress (updates every 10 records)
- ✅ Success summary
- ⚠️ Any errors/skipped records

Example output:
```
📋 Exporting Devfolio hackathons to "devfolio" table
🔌 Connecting to Supabase...
✅ Connected to Supabase!
✅ Table "devfolio" ready
🔍 Fetching existing URLs from Supabase...
✅ Found 50 existing records in Supabase
📊 Found 100 total records
📊 After filtering: 50 new records to export (sorted by date)
⏳ Progress: 50/50

✅ Export completed!
  📈 New records added: 50
  📊 Total in Supabase: 100

🔌 Connection closed.
```

## Environment Setup

Make sure your `.env` file contains:
```
SUPABASE_PASSWORD=your_password_here
```

## Troubleshooting

### Error: SUPABASE_PASSWORD not found
Add your Supabase password to `.env` file.

### Error: Table does not exist
Run the schema creation script first:
```bash
python create_devfolio_supabase_schema.py
```

### Error: Duplicate key value
A record with that URL already exists. Use `--update-existing` to update it:
```bash
python manage.py export_to_supabase -d devfolio --update-existing
```

### No new records to export
All records are already in Supabase. Use `--update-existing` if you want to refresh existing data.

## Data Mapping

### Devfolio JSON to Database

```python
{
  "name": "Ethindia",                    → name
  "url": "https://...",                  → url
  "organizer": "Bengaluru",              → organizer
  "status": "past",                      → status
  "participants_count": "1418",          → participants_count
  "projects_count": null,                → projects_count
  "about_content": "...",                → about_content
  "start_date": "2018-08-10...",         → start_date
  "end_date": "2018-08-12...",           → end_date
  "location": "Bengaluru, ...",          → location
  "organizer_contact": "Email: ...",     → organizer_contact
  "important_dates": "Registration...",  → important_dates
  "official_website": "https://...",     → official_website
  "scraped_at": "2025-11-10...",         → scraped_at
  "updated_at": "2025-11-10...",         → updated_at
  
  // EXCLUDED FROM EXPORT:
  "prizes": null,                        → ❌ NOT STORED
  "themes": null,                        → ❌ NOT STORED
  "mode": "offline"                      → ❌ NOT STORED
}
```

## Best Practices

1. **Regular Updates**: Run incremental exports daily/weekly
2. **Monitor Logs**: Check for skipped records
3. **Verify Data**: Check Supabase after export
4. **Backup Before Clear**: Always backup before using `--clear`
5. **Use Sorting**: Export in organized order for better analysis

## Related Files

- `create_devfolio_supabase_schema.py` - Creates Devfolio table
- `scraper/management/commands/export_to_supabase.py` - Main export command
- `update_supabase_schema.py` - Updates Unstop table (legacy)

## See Also

- Main README for scraping commands
- DEVFOLIO_FEATURE.md for Devfolio scraping
- Database schema documentation in Supabase
