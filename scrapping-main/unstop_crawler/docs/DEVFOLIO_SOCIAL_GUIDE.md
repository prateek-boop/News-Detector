# Devfolio Social Media Extraction - Complete Guide

Complete guide for extracting and managing social media links from Devfolio hackathons.

## Overview

This feature extracts social media links (Telegram, Discord, LinkedIn, Twitter) from Devfolio hackathon pages and stores them in separate columns for easy access and analysis.

---

## Table of Contents

1. [Database Schema](#database-schema)
2. [Extraction Commands](#extraction-commands)
3. [Supabase Integration](#supabase-integration)
4. [Workflows](#workflows)
5. [Troubleshooting](#troubleshooting)

---

## Database Schema

### Local SQLite (DevfolioHackathon model)

New fields added:
- `telegram_link` - Telegram group/channel links
- `discord_link` - Discord server invite links
- `linkedin_link` - LinkedIn profile/company pages
- `twitter_link` - Twitter/X profile links

### Supabase PostgreSQL (Devfolio table)

Same columns with VARCHAR(500) type for all social media links.

---

## Extraction Commands

### 1. Extract Social Media Links

Extract social media links from Devfolio hackathon pages.

```bash
# Extract from all hackathons
python manage.py extract_devfolio_social --all

# Extract only from hackathons missing social links
python manage.py extract_devfolio_social --missing-only

# Extract from specific URL
python manage.py extract_devfolio_social --url https://devfolio.co/hackathons/example

# Extract from specific database ID
python manage.py extract_devfolio_social --id 5

# Limit to first 20 hackathons
python manage.py extract_devfolio_social --all --limit 20
```

**What it extracts:**
- ✓ Telegram links (t.me, telegram.me)
- ✓ Discord invites (discord.gg, discord.com/invite)
- ✓ LinkedIn pages (linkedin.com)
- ✓ Twitter/X profiles (twitter.com, x.com)

**How it works:**
1. Opens hackathon page with Selenium
2. Scans all links on the page
3. Pattern matches for social media platforms
4. Also checks page text for embedded links
5. Updates database with found links

---

## Supabase Integration

### Step 1: Add Social Media Columns to Supabase

```bash
# Add columns to Devfolio table in Supabase
python manage.py add_devfolio_social_columns

# Check if columns exist (dry run)
python manage.py add_devfolio_social_columns --check-only
```

**What it does:**
- Connects to Supabase
- Checks if Devfolio table exists
- Adds missing social media columns
- Verifies columns were added

**Columns added:**
```sql
ALTER TABLE "Devfolio"
ADD COLUMN IF NOT EXISTS "telegram_link" VARCHAR(500);
ADD COLUMN IF NOT EXISTS "discord_link" VARCHAR(500);
ADD COLUMN IF NOT EXISTS "linkedin_link" VARCHAR(500);
ADD COLUMN IF NOT EXISTS "twitter_link" VARCHAR(500);
```

### Step 2: Export Data to Supabase

```bash
# Export all Devfolio data including social links
python manage.py export_devfolio_to_supabase

# Clear and re-export
python manage.py export_devfolio_to_supabase --clear

# Export with sorting
python manage.py export_devfolio_to_supabase --sort name
python manage.py export_devfolio_to_supabase --sort date
python manage.py export_devfolio_to_supabase --sort participants
```

**Features:**
- Upserts data (INSERT or UPDATE on conflict)
- Handles field truncation automatically
- Individual transaction per record (robust)
- Progress reporting every 10 records

---

## Complete Workflows

### Workflow 1: Initial Setup (New System)

```bash
# Step 1: Scrape Devfolio hackathons
python manage.py scrape_devfolio --limit 50

# Step 2: Extract social media links
python manage.py extract_devfolio_social --all

# Step 3: Setup Supabase schema
python manage.py add_devfolio_social_columns

# Step 4: Export to Supabase
python manage.py export_devfolio_to_supabase
```

### Workflow 2: Update Existing Data

```bash
# Step 1: Extract missing social links
python manage.py extract_devfolio_social --missing-only

# Step 2: Sync to Supabase
python manage.py export_devfolio_to_supabase
```

### Workflow 3: Fresh Re-extraction

```bash
# Step 1: Re-extract all social links (overwrite existing)
python manage.py extract_devfolio_social --all

# Step 2: Clear and re-export to Supabase
python manage.py export_devfolio_to_supabase --clear
```

### Workflow 4: Single Hackathon Update

```bash
# Update specific hackathon
python manage.py extract_devfolio_social --url https://devfolio.co/hackathons/example

# Sync to Supabase
python manage.py export_devfolio_to_supabase
```

---

## Data Examples

### Example Output from Extraction

```
[1/50] Processing: HackMIT 2024
  URL: https://devfolio.co/hackathons/hackmit-2024
  ✓ Updated: Telegram, Discord, Twitter
  
[2/50] Processing: ETHIndia 2024
  URL: https://devfolio.co/hackathons/ethindia-2024
  ✓ Updated: Discord, LinkedIn
  
[3/50] Processing: DevHacks 2024
  URL: https://devfolio.co/hackathons/devhacks-2024
  ○ No social links found
```

### Example Database Records

```python
# After extraction
hackathon = DevfolioHackathon.objects.get(name="HackMIT 2024")
print(hackathon.telegram_link)  # https://t.me/hackmit2024
print(hackathon.discord_link)   # https://discord.gg/hackmit
print(hackathon.linkedin_link)  # https://linkedin.com/company/hackmit
print(hackathon.twitter_link)   # https://twitter.com/hackmit
```

---

## Command Reference

### extract_devfolio_social

**Purpose:** Extract social media links from Devfolio pages

**Options:**
- `--all` - Process all hackathons
- `--missing-only` - Only process hackathons without social links
- `--url URL` - Process specific URL
- `--id ID` - Process specific database ID
- `--limit N` - Limit to N hackathons

**Time:** ~4-5 seconds per hackathon (includes page load)

### add_devfolio_social_columns

**Purpose:** Add social media columns to Supabase Devfolio table

**Options:**
- `--check-only` - Check without adding columns

**Time:** < 1 second

### export_devfolio_to_supabase

**Purpose:** Export Devfolio data to Supabase including social links

**Options:**
- `--clear` - Clear existing data before export
- `--sort {name,date,participants}` - Sort order

**Time:** ~0.5 seconds per record

---

## Tips & Best Practices

1. **Start Small**
   - Test with `--limit 10` first
   - Verify extraction quality before processing all

2. **Use Missing-Only**
   - For updates, use `--missing-only` to save time
   - Only re-extracts hackathons without social links

3. **Monitor Progress**
   - Commands show detailed progress
   - Watch for "No social links found" patterns

4. **Supabase Setup**
   - Run `add_devfolio_social_columns` only once
   - Use `--check-only` to verify schema

5. **Regular Sync**
   - Extract social links after scraping new hackathons
   - Export to Supabase regularly for backup

---

## Troubleshooting

### Problem: No social links found

**Cause:** Hackathon page doesn't have social links or they're loaded dynamically

**Solution:**
- Check the hackathon page manually
- Links might be in images or embedded content
- Some hackathons genuinely don't have social media

### Problem: Extraction is slow

**Cause:** Selenium loads full pages

**Solution:**
- Use `--limit` to process in batches
- Run overnight for large datasets
- ~4-5 seconds per page is normal

### Problem: Supabase column already exists error

**Cause:** Columns were added in a previous run

**Solution:**
- This is safe to ignore
- Use `--check-only` to verify

### Problem: Wrong links extracted

**Cause:** Page contains multiple links to same platform

**Solution:**
- First link found is used
- Check page source if links are incorrect
- Manual verification recommended for critical data

---

## Advanced Usage

### Custom Extraction Patterns

The extraction uses regex patterns. To modify, edit `extract_devfolio_social.py`:

```python
# Telegram patterns
if 't.me' in href or 'telegram.me' in href:
    social_links['telegram'] = href

# Discord patterns
if 'discord.gg' in href or 'discord.com/invite' in href:
    social_links['discord'] = href
```

### Batch Processing

```bash
# Process in batches of 50
for i in {1..10}; do
    python manage.py extract_devfolio_social --all --limit 50
    sleep 10
done
```

### Export Filtering

Modify SQL query in `export_devfolio_to_supabase.py` to export only hackathons with social links:

```python
hackathons = DevfolioHackathon.objects.exclude(
    telegram_link__isnull=True,
    discord_link__isnull=True
)
```

---

## Database Schema Details

### Local SQLite Migration

```python
# Migration 0006
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='devfoliohackathon',
            name='discord_link',
            field=models.URLField(blank=True, null=True),
        ),
        # ... (telegram_link, linkedin_link, twitter_link)
    ]
```

### Supabase Table Structure

```sql
CREATE TABLE "Devfolio" (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500),
    url VARCHAR(500) UNIQUE NOT NULL,
    -- ... other fields ...
    telegram_link VARCHAR(500),
    discord_link VARCHAR(500),
    linkedin_link VARCHAR(500),
    twitter_link VARCHAR(500),
    scraped_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

---

## Summary

✅ **What's Added:**
- 4 new database fields for social media links
- Automated extraction from Devfolio pages
- Supabase schema update command
- Export with social media data

✅ **Commands:**
- `extract_devfolio_social` - Extract links
- `add_devfolio_social_columns` - Update Supabase schema
- `export_devfolio_to_supabase` - Sync to Supabase

✅ **Features:**
- Pattern matching for all major platforms
- Robust error handling
- Progress reporting
- Individual transaction commits

🎯 **Use Case:**
Perfect for hackathon organizers, participants, and researchers who need quick access to hackathon community channels and social media presence.

---

**Need Help?** Run any command with `--help` for detailed usage information.
