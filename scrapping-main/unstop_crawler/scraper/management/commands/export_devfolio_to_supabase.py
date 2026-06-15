import psycopg2
from django.core.management.base import BaseCommand
from scraper.models import DevfolioHackathon
from dotenv import load_dotenv
import os

load_dotenv()


class Command(BaseCommand):
    help = """
    Export Devfolio hackathon data to Supabase PostgreSQL.
    
    Syncs local Devfolio database with Supabase including social media links.
    
    USAGE:
    
      # Export all Devfolio hackathons
      python manage.py export_devfolio_to_supabase
      
      # Clear and re-export
      python manage.py export_devfolio_to_supabase --clear
      
      # Export with sorting
      python manage.py export_devfolio_to_supabase --sort name
    
    EXAMPLES:
    
      # Regular export
      python manage.py export_devfolio_to_supabase
      
      # Fresh start
      python manage.py export_devfolio_to_supabase --clear
      
      # Sort by participants
      python manage.py export_devfolio_to_supabase --sort participants
    
    OPTIONS:
      --clear       Clear existing data before export
      --sort TEXT   Sort order (name, date, participants)
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
            CREATE TABLE IF NOT EXISTS "Devfolio" (
                id SERIAL PRIMARY KEY,
                name VARCHAR(500),
                url VARCHAR(500) UNIQUE NOT NULL,
                organizer VARCHAR(500),
                status VARCHAR(50),
                participants_count VARCHAR(100),
                projects_count VARCHAR(100),
                about_content TEXT,
                organizer_contact TEXT,
                important_dates TEXT,
                start_date VARCHAR(200),
                end_date VARCHAR(200),
                location VARCHAR(500),
                mode VARCHAR(100),
                prizes TEXT,
                themes TEXT,
                official_website VARCHAR(500),
                telegram_link VARCHAR(500),
                discord_link VARCHAR(500),
                linkedin_link VARCHAR(500),
                twitter_link VARCHAR(500),
                scraped_at TIMESTAMP,
                updated_at TIMESTAMP
            );
            """
            cursor.execute(create_table_query)
            connection.commit()
            self.stdout.write(self.style.SUCCESS('Table "Devfolio" ready'))

            # Clear existing data if requested
            if options['clear']:
                cursor.execute('DELETE FROM "Devfolio";')
                connection.commit()
                self.stdout.write(self.style.WARNING('Cleared existing data'))

            # Get hackathons with sorting
            sort_by = options['sort']
            if sort_by == 'name':
                hackathons = DevfolioHackathon.objects.all().order_by('name')
                sort_desc = "alphabetically by name"
            elif sort_by == 'participants':
                hackathons = DevfolioHackathon.objects.all().order_by('-scraped_at')
                sort_desc = "by participants (sorting in Python)"
            else:  # date
                hackathons = DevfolioHackathon.objects.all().order_by('-scraped_at')
                sort_desc = "by date (most recent first)"

            total = hackathons.count()
            self.stdout.write(f'Found {total} records to export (sorted {sort_desc})')

            # Insert data
            inserted = 0
            skipped = 0

            insert_query = """
            INSERT INTO "Devfolio" (
                name, url, organizer, status, participants_count, projects_count,
                about_content, organizer_contact, important_dates,
                start_date, end_date, location, mode, prizes, themes,
                official_website, telegram_link, discord_link, 
                linkedin_link, twitter_link, scraped_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
                name = EXCLUDED.name,
                organizer = EXCLUDED.organizer,
                status = EXCLUDED.status,
                participants_count = EXCLUDED.participants_count,
                projects_count = EXCLUDED.projects_count,
                about_content = EXCLUDED.about_content,
                organizer_contact = EXCLUDED.organizer_contact,
                important_dates = EXCLUDED.important_dates,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                location = EXCLUDED.location,
                mode = EXCLUDED.mode,
                prizes = EXCLUDED.prizes,
                themes = EXCLUDED.themes,
                official_website = EXCLUDED.official_website,
                telegram_link = EXCLUDED.telegram_link,
                discord_link = EXCLUDED.discord_link,
                linkedin_link = EXCLUDED.linkedin_link,
                twitter_link = EXCLUDED.twitter_link,
                updated_at = EXCLUDED.updated_at;
            """

            for hackathon in hackathons:
                try:
                    # Truncate fields that might be too long
                    name = (hackathon.name or '')[:500]
                    organizer = (hackathon.organizer or '')[:500]
                    status = (hackathon.status or '')[:50]
                    participants_count = (hackathon.participants_count or '')[:100]
                    projects_count = (hackathon.projects_count or '')[:100]
                    location = (hackathon.location or '')[:500]
                    mode = (hackathon.mode or '')[:100]
                    official_website = (hackathon.official_website or '')[:500]
                    telegram_link = (hackathon.telegram_link or '')[:500]
                    discord_link = (hackathon.discord_link or '')[:500]
                    linkedin_link = (hackathon.linkedin_link or '')[:500]
                    twitter_link = (hackathon.twitter_link or '')[:500]

                    cursor.execute(insert_query, (
                        name,
                        hackathon.url,
                        organizer,
                        status,
                        participants_count,
                        projects_count,
                        hackathon.about_content,
                        hackathon.organizer_contact,
                        hackathon.important_dates,
                        hackathon.start_date,
                        hackathon.end_date,
                        location,
                        mode,
                        hackathon.prizes,
                        hackathon.themes,
                        official_website,
                        telegram_link,
                        discord_link,
                        linkedin_link,
                        twitter_link,
                        hackathon.scraped_at,
                        hackathon.updated_at,
                    ))
                    connection.commit()
                    inserted += 1

                    if inserted % 10 == 0:
                        self.stdout.write(f'Progress: {inserted}/{total}')

                except Exception as e:
                    connection.rollback()
                    skipped += 1
                    error_msg = str(e).split('\n')[0]
                    self.stdout.write(self.style.WARNING(f'Skipped: {hackathon.name[:50]} - {error_msg}'))

            # Summary
            self.stdout.write(self.style.SUCCESS(f'\n✓ Export completed!'))
            self.stdout.write(self.style.SUCCESS(f'  Inserted/Updated: {inserted}'))
            if skipped > 0:
                self.stdout.write(self.style.WARNING(f'  Skipped: {skipped}'))

            # Show total records in Supabase
            cursor.execute('SELECT COUNT(*) FROM "Devfolio";')
            count = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(f'  Total in Supabase: {count}'))

            cursor.close()
            connection.close()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            traceback.print_exc()
