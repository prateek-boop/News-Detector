import os
import psycopg2
from django.core.management.base import BaseCommand
from django.conf import settings
from contacts.models import Contact
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class Command(BaseCommand):
    help = 'Export contacts to Supabase database (table: linkedin)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be exported without actually exporting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be exported'))
        
        # Supabase configuration
        supabase_config = {
            'host': os.getenv('SUPABASE_HOST'),
            'port': os.getenv('SUPABASE_PORT'),
            'dbname': os.getenv('SUPABASE_DBNAME'),
            'user': os.getenv('SUPABASE_USER'),
            'password': os.getenv('SUPABASE_PASSWORD')
        }
        
        # Validate configuration
        if not all(supabase_config.values()):
            self.stdout.write(self.style.ERROR('Missing Supabase configuration in .env file'))
            return
        
        try:
            # Get all contacts from Django DB
            contacts = Contact.objects.all()
            total_contacts = contacts.count()
            
            if total_contacts == 0:
                self.stdout.write(self.style.WARNING('No contacts found in database'))
                return
            
            self.stdout.write(f'Found {total_contacts} contacts in Django database')
            
            if dry_run:
                self.stdout.write('\nContacts that would be exported:')
                for contact in contacts[:10]:
                    self.stdout.write(f'  - {contact.name or "N/A"} ({contact.email})')
                if total_contacts > 10:
                    self.stdout.write(f'  ... and {total_contacts - 10} more')
                return
            
            # Connect to Supabase
            self.stdout.write('Connecting to Supabase...')
            conn = psycopg2.connect(**supabase_config)
            self.stdout.write(self.style.SUCCESS('Connected to Supabase'))
            
            try:
                # Create table if not exists
                self._create_table(conn)
                
                # Get existing emails
                existing_emails = self._get_existing_emails(conn)
                self.stdout.write(f'Found {len(existing_emails)} existing records in Supabase')
                
                # Export contacts
                new_count = 0
                skipped_count = 0
                error_count = 0
                
                for contact in contacts:
                    if contact.email in existing_emails:
                        skipped_count += 1
                        self.stdout.write(f'Skipped (exists): {contact.email}')
                    else:
                        result = self._insert_contact(conn, contact)
                        if result == 'inserted':
                            new_count += 1
                            self.stdout.write(self.style.SUCCESS(f'Inserted: {contact.name or "N/A"} - {contact.email}'))
                            existing_emails.add(contact.email)
                        elif result == 'duplicate':
                            skipped_count += 1
                            self.stdout.write(f'Skipped (already exists): {contact.email}')
                            existing_emails.add(contact.email)
                        else:
                            error_count += 1
                            self.stdout.write(self.style.ERROR(f'Failed: {contact.email}'))
                
                # Summary
                self.stdout.write('\n' + '='*60)
                self.stdout.write(self.style.SUCCESS('Export Summary:'))
                self.stdout.write(f'  Total contacts in Django: {total_contacts}')
                self.stdout.write(self.style.SUCCESS(f'  New records inserted: {new_count}'))
                self.stdout.write(self.style.WARNING(f'  Duplicates skipped: {skipped_count}'))
                if error_count > 0:
                    self.stdout.write(self.style.ERROR(f'  Errors: {error_count}'))
                self.stdout.write('='*60)
                
            finally:
                conn.close()
                self.stdout.write('Database connection closed')
                
        except psycopg2.Error as e:
            self.stdout.write(self.style.ERROR(f'Database error: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
    
    def _create_table(self, conn):
        """Create linkedin table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS linkedin (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE,
            name VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        with conn.cursor() as cur:
            cur.execute(create_table_query)
            conn.commit()
        self.stdout.write(self.style.SUCCESS("✓ Table 'linkedin' ready"))
    
    def _get_existing_emails(self, conn):
        """Fetch all existing emails from Supabase"""
        with conn.cursor() as cur:
            cur.execute("SELECT email FROM linkedin WHERE email IS NOT NULL")
            return {row[0] for row in cur.fetchall()}
    
    def _insert_contact(self, conn, contact):
        """Insert a contact into Supabase"""
        insert_query = """
        INSERT INTO linkedin (email, name, created_at, updated_at)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (email) DO NOTHING
        RETURNING id;
        """
        
        try:
            with conn.cursor() as cur:
                now = datetime.now()
                cur.execute(insert_query, (
                    contact.email,
                    contact.name,
                    now,
                    now
                ))
                result = cur.fetchone()
                conn.commit()
                
                if result is not None:
                    return 'inserted'
                else:
                    return 'duplicate'
        except psycopg2.IntegrityError as e:
            self.stdout.write(self.style.WARNING(f'Integrity error for {contact.email}: {e}'))
            conn.rollback()
            return 'error'
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error inserting {contact.email}: {str(e)[:100]}'))
            conn.rollback()
            return 'error'
