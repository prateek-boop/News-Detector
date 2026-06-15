# Supabase Export Guide

## Overview

Three commands to export data from local Django database to Supabase PostgreSQL:

1. `export_to_supabase` - Export contacts (emails) only
2. `export_profiles_to_supabase` - Export profiles (LinkedIn URLs) only
3. `export_all_to_supabase` - Export everything in one command

## Prerequisites

Make sure your `.env` file contains Supabase credentials:

```env
SUPABASE_HOST=db.rxdloipxqvjldsftitcn.supabase.co
SUPABASE_PORT=5432
SUPABASE_DBNAME=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=your_password
```

## Commands

### Export All (Recommended)

Export both contacts and profiles in one command:

```bash
# Dry run (safe test)
python manage.py export_all_to_supabase --dry-run

# Export everything
python manage.py export_all_to_supabase

# Export only contacts
python manage.py export_all_to_supabase --skip-profiles

# Export only profiles
python manage.py export_all_to_supabase --skip-contacts
```

### Export Contacts Only

```bash
# Dry run
python manage.py export_to_supabase --dry-run

# Export
python manage.py export_to_supabase
```

### Export Profiles Only

```bash
# Dry run
python manage.py export_profiles_to_supabase --dry-run

# Export
python manage.py export_profiles_to_supabase
```

## Database Tables

### Table: linkedin (Contacts)

```sql
CREATE TABLE linkedin (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Table: linkedin_profiles (Profiles)

```sql
CREATE TABLE linkedin_profiles (
    id SERIAL PRIMARY KEY,
    linkedin_url VARCHAR(500) UNIQUE NOT NULL,
    contact_email VARCHAR(255),
    scraped_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_linkedin_profiles_url ON linkedin_profiles(linkedin_url);
CREATE INDEX idx_linkedin_profiles_email ON linkedin_profiles(contact_email);
```

## Features

### Automatic Table Creation

All commands automatically create tables if they don't exist. No manual SQL needed.

### Duplicate Prevention

All commands check for existing records before inserting:
- Contacts: Checked by email
- Profiles: Checked by linkedin_url
- Duplicates are skipped, not re-inserted

### Dry Run Mode

Test exports without actually inserting data:

```bash
python manage.py export_all_to_supabase --dry-run
```

Shows what would be exported without making changes.

### Progress Tracking

Real-time output shows:
- Number of records found locally
- Number of existing records in Supabase
- Each insert/skip operation
- Final summary with counts

## Example Output

### Export All Command

```
======================================================================
Supabase Complete Export
======================================================================

Local Database:
  Contacts: 10147
  Profiles: 20

======================================================================
PART 1: Exporting Contacts
======================================================================

Found 10147 contacts in Django database
Connecting to Supabase...
Connected to Supabase
Found 5000 existing records in Supabase
Inserted: john@example.com
Inserted: jane@example.com
Skipped (exists): existing@example.com
...

============================================================
Export Summary:
  Total contacts in Django: 10147
  New records inserted: 5147
  Duplicates skipped: 5000
============================================================

======================================================================
PART 2: Exporting Profiles
======================================================================

Found 20 profiles in Django database
Connecting to Supabase...
Connected to Supabase
Found 0 existing profiles in Supabase
Inserted: https://www.linkedin.com/in/johndoe
Inserted: https://www.linkedin.com/in/janedoe
...

============================================================
Export Summary:
  Total profiles in Django: 20
  New records inserted: 20
  Duplicates skipped: 0
============================================================

======================================================================
COMPLETE EXPORT SUMMARY
======================================================================

Local Database:
  Contacts: 10147
  Profiles: 20

Supabase Database:
  Contacts: 10147
  Profiles: 20

All data synced successfully!

======================================================================
Export Complete!
======================================================================
```

## Verification

### Check Supabase Dashboard

1. Go to Supabase dashboard
2. Navigate to Table Editor
3. Check tables:
   - `linkedin` for contacts
   - `linkedin_profiles` for profiles

### SQL Queries

```sql
-- Count contacts
SELECT COUNT(*) FROM linkedin;

-- Count profiles
SELECT COUNT(*) FROM linkedin_profiles;

-- View sample contacts
SELECT * FROM linkedin LIMIT 10;

-- View sample profiles
SELECT * FROM linkedin_profiles LIMIT 10;

-- Join contacts with profiles
SELECT 
    l.email,
    l.name,
    lp.linkedin_url,
    lp.scraped_at
FROM linkedin l
LEFT JOIN linkedin_profiles lp ON l.email = lp.contact_email
LIMIT 10;
```

## Troubleshooting

### Connection Error

```
Database error: could not connect to server
```

Solution:
- Check .env credentials
- Verify Supabase project is running
- Check network connection
- Verify IP is allowed in Supabase settings

### Missing Configuration

```
Missing Supabase configuration in .env file
```

Solution:
- Ensure all SUPABASE_* variables are set in .env
- Check for typos in variable names
- Make sure .env file is in project root

### Table Creation Error

```
Error creating table: permission denied
```

Solution:
- Verify database user has CREATE TABLE permission
- Use postgres user (has full permissions)
- Check Supabase user roles

### Duplicate Key Error

This should not happen as duplicates are handled. If it does:
- Check if multiple exports are running simultaneously
- Verify unique constraints exist
- Use --dry-run to test first

## Best Practices

### Regular Exports

Export after each scraping session:

```bash
# After scraping
python manage.py scrape_all --url "POST_URL"

# Export to Supabase
python manage.py export_all_to_supabase
```

### Scheduled Exports

Set up a cron job or scheduled task:

```bash
# Daily export at 2 AM
0 2 * * * cd /path/to/project && python manage.py export_all_to_supabase
```

### Backup Before Export

```bash
# Backup local database
cp db.sqlite3 db.sqlite3.backup

# Export
python manage.py export_all_to_supabase
```

### Incremental Exports

Only new data is exported due to duplicate checking. Run as often as needed without worrying about duplicates.

## Data Sync Strategy

### After Each Scraping Run

```bash
python manage.py scrape_all --url "POST_URL"
python manage.py export_all_to_supabase
```

### Bulk Export

If you have accumulated data:

```bash
# Export everything at once
python manage.py export_all_to_supabase
```

### Verify Sync

```bash
# Check counts match
python manage.py export_all_to_supabase --dry-run
```

## Advanced Usage

### Export Only New Profiles

Since duplicate checking is automatic:

```bash
# Run anytime, only new profiles exported
python manage.py export_profiles_to_supabase
```

### Re-export After Cleanup

If you clean local database:

```bash
# Clear local profiles
python manage.py shell -c "from contacts.models import Profile; Profile.objects.all().delete()"

# Scrape again
python manage.py scrape_all --url "POST_URL"

# Export new data
python manage.py export_all_to_supabase
```

## Monitoring

### Check Export History

Query Supabase to see when data was added:

```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as records_added
FROM linkedin
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

### Track Growth

```sql
SELECT 
    COUNT(*) as total_contacts,
    COUNT(DISTINCT SUBSTRING(email FROM POSITION('@' IN email) + 1)) as unique_domains
FROM linkedin;
```

## Integration with Infinite Loop

When running infinite scraper:

```python
# In scrape_infinite.py
if posts_scraped % 10 == 0:
    # Export every 10 posts
    call_command('export_all_to_supabase')
```

This ensures data is backed up to Supabase regularly during long-running scrapes.

## Help

View command help:

```bash
python manage.py export_all_to_supabase --help
python manage.py export_to_supabase --help
python manage.py export_profiles_to_supabase --help
```
