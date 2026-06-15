# Update Supabase Database Schema

## Quick Steps

### Option 1: Using Supabase Dashboard (Recommended)

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Select your project

2. **Open SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New query"

3. **Run the Migration**
   - Copy the contents of `supabase_migration.sql`
   - Paste into the SQL Editor
   - Click "Run" or press Ctrl+Enter

4. **Verify Success**
   - You should see a table showing all columns including the new ones
   - Look for `impression_count` and `registration_count`

### Option 2: Using Python Script

Run the automated script:

```bash
cd /home/sonu/Desktop/unstop_crawler
source .venv/bin/activate
python update_supabase_schema.py
```

---

## After Adding Columns

### Export Your Updated Data to Supabase

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Export all data to Supabase (this will update the schema automatically)
python manage.py export_to_supabase
```

The export script has already been updated to include the new fields, so it will work immediately after you add the columns.

---

## Verify the Update

Run this in Supabase SQL Editor to check:

```sql
-- Check the table structure
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'Unstop' 
ORDER BY ordinal_position;

-- Check if data is being populated
SELECT 
    name,
    registered_count,
    registration_count,
    impression_count
FROM "Unstop"
LIMIT 5;
```

---

## Troubleshooting

### "Column already exists" error
This is fine - the migration uses `IF NOT EXISTS` to prevent errors.

### Permission denied
Make sure you're logged in with the correct Supabase account that has admin access.

### Can't connect to Supabase
Check that your `SUPABASE_PASSWORD` is set correctly in the `.env` file.

---

## Summary

1. ✅ Run `supabase_migration.sql` in Supabase SQL Editor
2. ✅ Run `python manage.py export_to_supabase` to sync data
3. ✅ Verify columns exist and data is populated

That's it! Your Supabase database will now have the new columns.
