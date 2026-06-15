import os
import psycopg2
from django.core.management.base import BaseCommand
from contacts.models import Profile
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class Command(BaseCommand):
    help = 'Export LinkedIn profiles to Supabase database (table: linkedin_profiles)'

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
            # Get all profiles from Django DB
            profiles = Profile.objects.all()
            total_profiles = profiles.count()
            
            if total_profiles == 0:
                self.stdout.write(self.style.WARNING('No profiles found in database'))
                return
            
            self.stdout.write(f'Found {total_profiles} profiles in Django database')
            
            if dry_run:
                self.stdout.write('\nProfiles that would be exported:')
                for profile in profiles[:10]:
                    contact_email = profile.contact.email if profile.contact else 'N/A'
                    self.stdout.write(f'  - {profile.linkedin_url} (Contact: {contact_email})')
                if total_profiles > 10:
                    self.stdout.write(f'  ... and {total_profiles - 10} more')
                return
            
            # Connect to Supabase
            self.stdout.write('Connecting to Supabase...')
            conn = psycopg2.connect(**supabase_config)
            self.stdout.write(self.style.SUCCESS('Connected to Supabase'))
            
            try:
                # Create table if not exists
                self._create_table(conn)
                
                # Get existing profile URLs
                existing_urls = self._get_existing_urls(conn)
                self.stdout.write(f'Found {len(existing_urls)} existing profiles in Supabase')
                
                # Export profiles
                new_count = 0
                skipped_count = 0
                error_count = 0
                
                for profile in profiles:
                    if profile.linkedin_url in existing_urls:
                        skipped_count += 1
                        self.stdout.write(f'Skipped (exists): {profile.linkedin_url}')
                    else:
                        result = self._insert_profile(conn, profile)
                        if result == 'inserted':
                            new_count += 1
                            self.stdout.write(self.style.SUCCESS(f'Inserted: {profile.linkedin_url}'))
                            existing_urls.add(profile.linkedin_url)
                        elif result == 'duplicate':
                            skipped_count += 1
                            self.stdout.write(f'Skipped (already exists): {profile.linkedin_url}')
                            existing_urls.add(profile.linkedin_url)
                        else:
                            error_count += 1
                            self.stdout.write(self.style.ERROR(f'Failed: {profile.linkedin_url}'))
                
                # Summary
                self.stdout.write('\n' + '='*60)
                self.stdout.write(self.style.SUCCESS('Export Summary:'))
                self.stdout.write(f'  Total profiles in Django: {total_profiles}')
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
        """Create linkedin_profiles table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS linkedin_profiles (
            id SERIAL PRIMARY KEY,
            linkedin_url VARCHAR(500) UNIQUE NOT NULL,
            contact_email VARCHAR(255),
            scraped_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_url ON linkedin_profiles(linkedin_url);
        CREATE INDEX IF NOT EXISTS idx_linkedin_profiles_email ON linkedin_profiles(contact_email);
        """
        
        try:
            cursor = conn.cursor()
            cursor.execute(create_table_query)
            conn.commit()
            cursor.close()
            self.stdout.write(self.style.SUCCESS('Table linkedin_profiles ready'))
        except psycopg2.Error as e:
            self.stdout.write(self.style.ERROR(f'Error creating table: {e}'))
            raise
    
    def _get_existing_urls(self, conn):
        """Get set of existing LinkedIn URLs from Supabase"""
        query = "SELECT linkedin_url FROM linkedin_profiles"
        
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            existing_urls = {row[0] for row in cursor.fetchall()}
            cursor.close()
            return existing_urls
        except psycopg2.Error as e:
            self.stdout.write(self.style.ERROR(f'Error fetching existing URLs: {e}'))
            return set()
    
    def _insert_profile(self, conn, profile):
        """Insert a profile into Supabase"""
        insert_query = """
        INSERT INTO linkedin_profiles (linkedin_url, contact_email, scraped_at)
        VALUES (%s, %s, %s)
        ON CONFLICT (linkedin_url) DO NOTHING
        RETURNING id
        """
        
        try:
            cursor = conn.cursor()
            contact_email = profile.contact.email if profile.contact else None
            scraped_at = profile.scraped_at if profile.scraped_at else datetime.now()
            
            cursor.execute(insert_query, (
                profile.linkedin_url,
                contact_email,
                scraped_at
            ))
            
            result = cursor.fetchone()
            conn.commit()
            cursor.close()
            
            return 'inserted' if result else 'duplicate'
        except psycopg2.IntegrityError:
            conn.rollback()
            return 'duplicate'
        except psycopg2.Error as e:
            conn.rollback()
            self.stdout.write(self.style.ERROR(f'Insert error: {e}'))
            return 'error'
