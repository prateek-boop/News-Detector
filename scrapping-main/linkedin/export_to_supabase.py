#!/usr/bin/env python3
"""
Export LinkedIn contacts data to Supabase
Checks for existing data before pushing to avoid duplicates
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Supabase connection parameters
SUPABASE_CONFIG = {
    'host': os.getenv('SUPABASE_HOST'),
    'port': os.getenv('SUPABASE_PORT'),
    'dbname': os.getenv('SUPABASE_DBNAME'),
    'user': os.getenv('SUPABASE_USER'),
    'password': os.getenv('SUPABASE_PASSWORD')
}

TABLE_NAME = 'linkedin'

def get_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(**SUPABASE_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        raise

def create_table_if_not_exists(conn):
    """Create linkedin table if it doesn't exist"""
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE,
        name VARCHAR(255),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    try:
        with conn.cursor() as cur:
            cur.execute(create_table_query)
            conn.commit()
            print(f"✓ Table '{TABLE_NAME}' ready")
    except Exception as e:
        print(f"Error creating table: {e}")
        conn.rollback()
        raise

def get_existing_emails(conn):
    """Fetch all existing emails from the database"""
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT email FROM {TABLE_NAME} WHERE email IS NOT NULL")
            existing_emails = {row[0] for row in cur.fetchall()}
            return existing_emails
    except Exception as e:
        print(f"Error fetching existing emails: {e}")
        return set()

def load_data_from_json(file_path):
    """Load data from JSON file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return []

def insert_contact(conn, email, name=None):
    """Insert a single contact into the database"""
    insert_query = f"""
    INSERT INTO {TABLE_NAME} (email, name, created_at, updated_at)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (email) DO NOTHING
    RETURNING id;
    """
    
    try:
        with conn.cursor() as cur:
            now = datetime.now()
            cur.execute(insert_query, (email, name, now, now))
            result = cur.fetchone()
            conn.commit()
            return result is not None
    except Exception as e:
        print(f"Error inserting contact {email}: {e}")
        conn.rollback()
        return False

def export_emails_to_supabase(data_file='linkedin_emails.json'):
    """Export email data to Supabase"""
    print(f"\n{'='*60}")
    print(f"Exporting data from {data_file} to Supabase")
    print(f"{'='*60}\n")
    
    # Load data
    data = load_data_from_json(data_file)
    if not data:
        print("No data to export")
        return
    
    print(f"Loaded {len(data)} records from {data_file}")
    
    # Connect to database
    conn = get_connection()
    print("✓ Connected to Supabase")
    
    try:
        # Create table if needed
        create_table_if_not_exists(conn)
        
        # Get existing emails
        existing_emails = get_existing_emails(conn)
        print(f"✓ Found {len(existing_emails)} existing records in database")
        
        # Process and insert data
        new_count = 0
        skipped_count = 0
        
        for record in data:
            email = record.get('email')
            if not email:
                continue
            
            if email in existing_emails:
                skipped_count += 1
                print(f"⊘ Skipped (exists): {email}")
            else:
                if insert_contact(conn, email):
                    new_count += 1
                    print(f"✓ Inserted: {email}")
                    existing_emails.add(email)
                else:
                    skipped_count += 1
        
        print(f"\n{'='*60}")
        print(f"Export Summary:")
        print(f"  Total records processed: {len(data)}")
        print(f"  New records inserted: {new_count}")
        print(f"  Duplicates skipped: {skipped_count}")
        print(f"{'='*60}\n")
        
    finally:
        conn.close()
        print("✓ Database connection closed")

def export_contacts_to_supabase(data_file='linkedin_contacts.json'):
    """Export contact data to Supabase"""
    print(f"\n{'='*60}")
    print(f"Exporting data from {data_file} to Supabase")
    print(f"{'='*60}\n")
    
    # Load data
    data = load_data_from_json(data_file)
    if not data:
        print("No data to export")
        return
    
    print(f"Loaded {len(data)} records from {data_file}")
    
    # Connect to database
    conn = get_connection()
    print("✓ Connected to Supabase")
    
    try:
        # Create table if needed
        create_table_if_not_exists(conn)
        
        # Get existing emails
        existing_emails = get_existing_emails(conn)
        print(f"✓ Found {len(existing_emails)} existing records in database")
        
        # Process and insert data
        new_count = 0
        skipped_count = 0
        
        for record in data:
            email = record.get('email')
            name = record.get('name')
            
            if not email:
                continue
            
            if email in existing_emails:
                skipped_count += 1
                print(f"⊘ Skipped (exists): {email}")
            else:
                if insert_contact(conn, email, name):
                    new_count += 1
                    print(f"✓ Inserted: {name or 'N/A'} - {email}")
                    existing_emails.add(email)
                else:
                    skipped_count += 1
        
        print(f"\n{'='*60}")
        print(f"Export Summary:")
        print(f"  Total records processed: {len(data)}")
        print(f"  New records inserted: {new_count}")
        print(f"  Duplicates skipped: {skipped_count}")
        print(f"{'='*60}\n")
        
    finally:
        conn.close()
        print("✓ Database connection closed")

def main():
    """Main function to run the export"""
    import sys
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        # Default to linkedin_contacts.json if it exists, else linkedin_emails.json
        if os.path.exists('linkedin_contacts.json'):
            data_file = 'linkedin_contacts.json'
        else:
            data_file = 'linkedin_emails.json'
    
    print(f"Using data file: {data_file}")
    
    if 'contacts' in data_file:
        export_contacts_to_supabase(data_file)
    else:
        export_emails_to_supabase(data_file)

if __name__ == "__main__":
    main()
