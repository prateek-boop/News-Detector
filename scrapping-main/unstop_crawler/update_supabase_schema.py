#!/usr/bin/env python3
"""
Update Supabase database schema to add new columns
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase connection details
HOST = "db.rxdloipxqvjldsftitcn.supabase.co"
PORT = "5432"
DBNAME = "postgres"
USER = "postgres"
PASSWORD = os.getenv("SUPABASE_PASSWORD")

def update_schema():
    if not PASSWORD:
        print("❌ Error: SUPABASE_PASSWORD not found in .env file")
        return False
    
    try:
        print("🔌 Connecting to Supabase...")
        connection = psycopg2.connect(
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
            dbname=DBNAME
        )
        cursor = connection.cursor()
        print("✅ Connected to Supabase!")
        
        # Add new columns
        print("\n📝 Adding new columns...")
        alter_query = """
        ALTER TABLE "Unstop" 
        ADD COLUMN IF NOT EXISTS "impression_count" VARCHAR(100),
        ADD COLUMN IF NOT EXISTS "registration_count" VARCHAR(100);
        """
        cursor.execute(alter_query)
        connection.commit()
        print("✅ Columns added successfully!")
        
        # Add comments
        print("\n📝 Adding column documentation...")
        comment_queries = [
            'COMMENT ON COLUMN "Unstop"."impression_count" IS \'Number of page views/impressions\';',
            'COMMENT ON COLUMN "Unstop"."registration_count" IS \'Actual number of participant registrations\';',
            'COMMENT ON COLUMN "Unstop"."registered_count" IS \'Legacy field - kept for backward compatibility\';',
        ]
        
        for query in comment_queries:
            cursor.execute(query)
        connection.commit()
        print("✅ Documentation added!")
        
        # Verify columns
        print("\n🔍 Verifying schema...")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length 
            FROM information_schema.columns 
            WHERE table_name = 'Unstop' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n📋 Current table structure:")
        print(f"{'Column Name':<30} {'Type':<20} {'Max Length':<15}")
        print("=" * 65)
        for col in columns:
            col_name, col_type, max_len = col
            max_len_str = str(max_len) if max_len else "N/A"
            print(f"{col_name:<30} {col_type:<20} {max_len_str:<15}")
        
        # Check for our new columns
        column_names = [col[0] for col in columns]
        if 'impression_count' in column_names and 'registration_count' in column_names:
            print("\n✅ SUCCESS! Both new columns are present in the database.")
            print("\n📤 Next step: Run this to sync your data:")
            print("   python manage.py export_to_supabase")
        else:
            print("\n⚠️ Warning: Some columns might be missing")
            if 'impression_count' not in column_names:
                print("   - impression_count not found")
            if 'registration_count' not in column_names:
                print("   - registration_count not found")
        
        cursor.close()
        connection.close()
        print("\n🔌 Connection closed.")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 65)
    print("   SUPABASE SCHEMA UPDATE - Add New Columns")
    print("=" * 65)
    
    success = update_schema()
    
    if success:
        print("\n" + "=" * 65)
        print("   ✅ SCHEMA UPDATE COMPLETED SUCCESSFULLY!")
        print("=" * 65)
    else:
        print("\n" + "=" * 65)
        print("   ❌ SCHEMA UPDATE FAILED")
        print("=" * 65)
