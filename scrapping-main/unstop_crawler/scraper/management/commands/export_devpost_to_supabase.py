import psycopg2
from django.core.management.base import BaseCommand
from scraper.models import DevpostHackathon
from dotenv import load_dotenv
import os

load_dotenv()


class Command(BaseCommand):
    help = """
    Export Devpost hackathon data to Supabase PostgreSQL.
    
    Syncs local Devpost database with Supabase (sorted alphabetically by name).
    
    USAGE:
    
      # Export all Devpost hackathons (sorted by name)
      python manage.py export_devpost_to_supabase
      
      # Clear and re-export
      python manage.py export_devpost_to_supabase --clear
      
      # Export with custom sorting
      python manage.py export_devpost_to_supabase --sort participants
    
    EXAMPLES:
    
      # Regular export (alphabetically sorted)
      python manage.py export_devpost_to_supabase
      
      # Fresh start
      python manage.py export_devpost_to_supabase --clear
      
      # Sort by participants
      python manage.py export_devpost_to_supabase --sort participants
    
    OPTIONS:
      --clear       Clear existing data before export
      --sort TEXT   Sort order (name, date, participants) - default: name
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data in Supabase before exporting',
        )
        parser.add_argument(
            '--sort',
            type=str,
            choices=['name', 'date', 'participants'],
            default='name',
            help='Sort order for export (default: name)',
        )

    def handle(self, *args, **options):
        HOST = "db.rxdloipxqvjldsftitcn.supabase.co"
        PORT = "5432"
        DBNAME = "postgres"
        USER = "postgres"
        PASSWORD = os.getenv("SUPABASE_PASSWORD")

        if not PASSWORD:
            self.stdout.write(self.style.ERROR('SUPABASE_PASSWORD not found in .env file'))
            return

        try:
            # Connect to Supabase
            self.stdout.write('Connecting to Supabase...')
            connection = psycopg2.connect(
                host=HOST,
                port=PORT,
                dbname=DBNAME,
                user=USER,
                password=PASSWORD
            )
            cursor = connection.cursor()
            self.stdout.write(self.style.SUCCESS('Connected to Supabase!'))

            # Create table if it doesn't exist
            create_table_query = """
            CREATE TABLE IF NOT EXISTS "Devpost" (
                id SERIAL PRIMARY KEY,
                name VARCHAR(500),
                url VARCHAR(500) UNIQUE NOT NULL,
                organizer VARCHAR(500),
                participants_count VARCHAR(100),
                about_content TEXT,
                organizer_contact TEXT,
                sponsors TEXT,
                scraped_at TIMESTAMP,
                updated_at TIMESTAMP
            );
            """
            cursor.execute(create_table_query)
            connection.commit()
            self.stdout.write('Table "Devpost" ready')

            # Clear table if requested
            if options['clear']:
                cursor.execute('DELETE FROM "Devpost";')
                connection.commit()
                self.stdout.write(self.style.WARNING('Cleared existing data'))

            # Get and sort data
            sort_by = options['sort']
            
            if sort_by == 'name':
                hackathons = DevpostHackathon.objects.all().order_by('name')
            elif sort_by == 'date':
                hackathons = DevpostHackathon.objects.all().order_by('-scraped_at')
            elif sort_by == 'participants':
                hackathons = list(DevpostHackathon.objects.all())
                hackathons.sort(key=lambda x: int(x.participants_count or '0'), reverse=True)
            
            if not isinstance(hackathons, list):
                hackathons = list(hackathons)

            total = len(hackathons)
            
            if total == 0:
                self.stdout.write(self.style.WARNING('No hackathons to export'))
                connection.close()
                return

            self.stdout.write(f'Found {total} records to export (sorted {sort_by}ly by {sort_by})')

            # Insert/update data
            insert_query = """
            INSERT INTO "Devpost" (name, url, organizer, participants_count, about_content, 
                                   organizer_contact, sponsors, scraped_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) 
            DO UPDATE SET
                name = EXCLUDED.name,
                organizer = EXCLUDED.organizer,
                participants_count = EXCLUDED.participants_count,
                about_content = EXCLUDED.about_content,
                organizer_contact = EXCLUDED.organizer_contact,
                sponsors = EXCLUDED.sponsors,
                updated_at = EXCLUDED.updated_at;
            """

            success_count = 0
            error_count = 0

            for idx, hackathon in enumerate(hackathons, 1):
                try:
                    cursor.execute(insert_query, (
                        hackathon.name,
                        hackathon.url,
                        hackathon.organizer,
                        hackathon.participants_count,
                        hackathon.about_content,
                        hackathon.organizer_contact,
                        hackathon.sponsors,
                        hackathon.scraped_at,
                        hackathon.updated_at,
                    ))
                    connection.commit()
                    success_count += 1
                    
                    # Progress update every 10 records
                    if idx % 10 == 0 or idx == total:
                        self.stdout.write(f'Progress: {idx}/{total}')
                    
                except Exception as e:
                    error_count += 1
                    error_msg = str(e)
                    # Only show first 100 chars of error
                    short_name = hackathon.name[:50] if hackathon.name else 'Unknown'
                    self.stdout.write(
                        self.style.ERROR(f'Skipped: {short_name} - {error_msg[:100]}')
                    )
                    connection.rollback()
                    continue

            # Summary
            self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
            self.stdout.write(self.style.SUCCESS(f'Export completed!'))
            self.stdout.write(f'  Successfully exported: {success_count}')
            self.stdout.write(f'  Errors: {error_count}')
            self.stdout.write(f'  Total processed: {total}')

            cursor.close()
            connection.close()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Database error: {str(e)}'))
