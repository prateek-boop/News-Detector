# Supabase Export & Security Setup

## Overview
Your SQLite database is now synced to Supabase PostgreSQL with Row Level Security (RLS) enabled.

## All 457 Records Exported ✓
All hackathon records from SQLite are in Supabase. The table uses URL as a unique key, so duplicate URLs are automatically updated instead of creating new records.

## Security Features

### Row Level Security (RLS)
- **Enabled**: Only authorized users can access data
- **Admin Access**: Full read/write/delete permissions
- **Read-Only Access**: Can only SELECT (view) data, cannot modify

### Authentication Required
The table is now restricted - only authenticated users can access it:

1. **Admin User** (Full Access)
   - Username: `postgres`
   - Password: `dKq?uc#djMTch6!`
   - Can: Read, Write, Update, Delete

2. **Read-Only User** (View Only)
   - Username: `unstop_reader`
   - Password: `sV6s&tGjvemIspbFqre@`
   - Can: Read only
   - Cannot: Insert, Update, or Delete

## Management Commands

### 1. Export Data to Supabase
```bash
# Basic export (upserts existing records)
python manage.py export_to_supabase

# Clear all data and re-export
python manage.py export_to_supabase --clear
```

### 2. Setup Security (One-time)
```bash
# Setup RLS and create read-only user
python manage.py setup_supabase_security

# With custom read-only password
python manage.py setup_supabase_security --readonly-password "your_password"
```

### 3. Test Access
```bash
# Test read-only user access
python manage.py test_supabase_access

# Test admin access
python manage.py test_supabase_access --admin
```

## Connection Details

### For Admin (Write Access)
```bash
psql -h db.rxdloipxqvjldsftitcn.supabase.co -p 5432 -d postgres -U postgres
```

### For Read-Only Access
```bash
psql -h db.rxdloipxqvjldsftitcn.supabase.co -p 5432 -d postgres -U unstop_reader
```

### Python Connection (Read-Only)
```python
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

connection = psycopg2.connect(
    host=os.getenv("SUPABASE_HOST"),
    port=os.getenv("SUPABASE_PORT"),
    database=os.getenv("SUPABASE_DBNAME"),
    user=os.getenv("SUPABASE_READONLY_USER"),
    password=os.getenv("SUPABASE_READONLY_PASSWORD")
)

cursor = connection.cursor()
cursor.execute("SELECT * FROM Unstop LIMIT 10;")
results = cursor.fetchall()
```

## Environment Variables (.env)
```env
# Supabase Admin Credentials
SUPABASE_HOST=db.rxdloipxqvjldsftitcn.supabase.co
SUPABASE_PORT=5432
SUPABASE_DBNAME=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=dKq?uc#djMTch6!

# Supabase Read-Only User
SUPABASE_READONLY_USER=unstop_reader
SUPABASE_READONLY_PASSWORD=sV6s&tGjvemIspbFqre@
```

## Table Schema
```sql
Table: Unstop

Columns:
- id                 SERIAL PRIMARY KEY
- name               VARCHAR(500) NOT NULL
- url                VARCHAR(200) UNIQUE NOT NULL
- organizer          VARCHAR(500)
- registered_count   VARCHAR(100)
- about_content      TEXT
- organizer_contact  TEXT
- important_dates    TEXT
- official_website   VARCHAR(200)
- scraped_at         TIMESTAMP NOT NULL
- updated_at         TIMESTAMP NOT NULL
```

## Security Best Practices

1. **Never commit .env file** - It's already in .gitignore
2. **Use read-only credentials** for public/client applications
3. **Use admin credentials** only for backend operations
4. **Rotate passwords** periodically using `setup_supabase_security`
5. **Monitor access** via Supabase dashboard

## Troubleshooting

### "Permission denied" error
- You're using read-only credentials for write operations
- Use admin credentials for exports/updates

### "Connection refused"
- Check internet connection
- Verify Supabase host is correct
- Check firewall settings

### Export showing 0 records
- Check SQLite database has data: `sqlite3 db.sqlite3 "SELECT COUNT(*) FROM scraper_hackathon;"`
- Verify Django settings are configured
