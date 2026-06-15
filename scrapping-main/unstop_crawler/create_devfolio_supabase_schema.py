#!/usr/bin/env python3
"""
Create Devfolio table in Supabase database
Based on the Unstop table schema but adapted for Devfolio data structure
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

def create_devfolio_schema():
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
        
        # Create Devfolio table
        print("\n📝 Creating Devfolio table...")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS public.devfolio (
            id SERIAL NOT NULL,
            name TEXT NOT NULL,
            url CHARACTER VARYING(500) NOT NULL,
            organizer TEXT NULL,
            status CHARACTER VARYING(50) NULL,
            participants_count CHARACTER VARYING(100) NULL,
            projects_count CHARACTER VARYING(100) NULL,
            about_content TEXT NULL,
            start_date TIMESTAMP WITH TIME ZONE NULL,
            end_date TIMESTAMP WITH TIME ZONE NULL,
            location TEXT NULL,
            organizer_contact TEXT NULL,
            important_dates TEXT NULL,
            official_website TEXT NULL,
            scraped_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            CONSTRAINT devfolio_pkey PRIMARY KEY (id),
            CONSTRAINT devfolio_url_key UNIQUE (url)
        ) TABLESPACE pg_default;
        """
        cursor.execute(create_table_query)
        connection.commit()
        print("✅ Table 'devfolio' created successfully!")
        
        # Add table comment
        print("\n📝 Adding table documentation...")
        cursor.execute("""
            COMMENT ON TABLE public.devfolio IS 'Devfolio hackathon data scraped from devfolio.co';
        """)
        
        # Add column comments
        comment_queries = [
            "COMMENT ON COLUMN public.devfolio.id IS 'Auto-incrementing primary key';",
            "COMMENT ON COLUMN public.devfolio.name IS 'Hackathon name/title';",
            "COMMENT ON COLUMN public.devfolio.url IS 'Devfolio hackathon URL (unique)';",
            "COMMENT ON COLUMN public.devfolio.organizer IS 'Organization or person hosting the hackathon';",
            "COMMENT ON COLUMN public.devfolio.status IS 'Hackathon status: open, past, upcoming';",
            "COMMENT ON COLUMN public.devfolio.participants_count IS 'Number of registered participants';",
            "COMMENT ON COLUMN public.devfolio.projects_count IS 'Number of submitted projects';",
            "COMMENT ON COLUMN public.devfolio.about_content IS 'Full description/about content';",
            "COMMENT ON COLUMN public.devfolio.start_date IS 'Hackathon start date and time';",
            "COMMENT ON COLUMN public.devfolio.end_date IS 'Hackathon end date and time';",
            "COMMENT ON COLUMN public.devfolio.location IS 'Event location or city';",
            "COMMENT ON COLUMN public.devfolio.organizer_contact IS 'Contact information for organizers';",
            "COMMENT ON COLUMN public.devfolio.important_dates IS 'Key dates and deadlines';",
            "COMMENT ON COLUMN public.devfolio.official_website IS 'External website URL';",
            "COMMENT ON COLUMN public.devfolio.scraped_at IS 'When the data was scraped';",
            "COMMENT ON COLUMN public.devfolio.updated_at IS 'Last update timestamp';",
        ]
        
        for query in comment_queries:
            cursor.execute(query)
        connection.commit()
        print("✅ Documentation added!")
        
        # Create indexes for better query performance
        print("\n📝 Creating indexes...")
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_devfolio_status ON public.devfolio(status);",
            "CREATE INDEX IF NOT EXISTS idx_devfolio_scraped_at ON public.devfolio(scraped_at DESC);",
            "CREATE INDEX IF NOT EXISTS idx_devfolio_organizer ON public.devfolio(organizer);",
            "CREATE INDEX IF NOT EXISTS idx_devfolio_start_date ON public.devfolio(start_date);",
        ]
        
        for query in index_queries:
            cursor.execute(query)
        connection.commit()
        print("✅ Indexes created!")
        
        # Verify table structure
        print("\n🔍 Verifying schema...")
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = 'devfolio' 
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n📋 Devfolio table structure:")
        print(f"{'Column Name':<25} {'Type':<25} {'Max Length':<12} {'Nullable':<10}")
        print("=" * 80)
        for col in columns:
            col_name, col_type, max_len, nullable = col
            max_len_str = str(max_len) if max_len else "N/A"
            print(f"{col_name:<25} {col_type:<25} {max_len_str:<12} {nullable:<10}")
        
        # Get row count
        cursor.execute("SELECT COUNT(*) FROM public.devfolio;")
        count = cursor.fetchone()[0]
        print(f"\n📊 Current records in table: {count}")
        
        print("\n✅ SUCCESS! Devfolio table is ready in Supabase.")
        print("\n📤 Next steps:")
        print("   1. Export Devfolio data:")
        print("      python manage.py export_to_supabase -d devfolio")
        print("\n   2. Or export Unstop data:")
        print("      python manage.py export_to_supabase -d unstop")
        
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
    print("=" * 80)
    print("   SUPABASE SCHEMA CREATION - Devfolio Table")
    print("=" * 80)
    
    success = create_devfolio_schema()
    
    if success:
        print("\n" + "=" * 80)
        print("   ✅ SCHEMA CREATION COMPLETED SUCCESSFULLY!")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("   ❌ SCHEMA CREATION FAILED")
        print("=" * 80)
