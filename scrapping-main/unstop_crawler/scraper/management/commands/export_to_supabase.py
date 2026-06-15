import psycopg2
from django.core.management.base import BaseCommand
from scraper.models import Hackathon, DevfolioHackathon
from dotenv import load_dotenv
import os

load_dotenv()


class Command(BaseCommand):
    help = """
    Export SQLite hackathon data to Supabase PostgreSQL.
    
    By DEFAULT, only exports NEW records not already in Supabase.
    This prevents duplicate uploads and is much faster for incremental updates.
    
    DESTINATIONS:
    
      -d unstop     Export Unstop hackathons to 'Unstop' table (default)
      -d devfolio   Export Devfolio hackathons to 'devfolio' table
    
    MODES:
    
    1. New Only (DEFAULT - Recommended):
       python manage.py export_to_supabase -d unstop
       - Only exports records not in Supabase
       - Fast and efficient
       - No duplicates
    
    2. Update Existing:
       python manage.py export_to_supabase -d devfolio --update-existing
       - Updates existing records
       - Adds new records
       - Slower but keeps data in sync
    
    3. Clear and Re-export:
       python manage.py export_to_supabase -d unstop --clear
       - Deletes all Supabase data first
       - Then exports everything
       - Fresh start
    
    EXAMPLES:
    
      # Export Unstop data (default)
      python manage.py export_to_supabase
      python manage.py export_to_supabase -d unstop
      
      # Export Devfolio data
      python manage.py export_to_supabase -d devfolio
      
      # Export and update existing records
      python manage.py export_to_supabase -d devfolio --update-existing
      
      # Clear Supabase and re-export all
      python manage.py export_to_supabase -d unstop --clear
      
      # Export with specific sorting
      python manage.py export_to_supabase -d devfolio --sort name
      python manage.py export_to_supabase -d unstop --sort registrations
    
    OPTIONS:
      -d, --destination {unstop,devfolio}  Target table (default: unstop)
      --new-only          Only export new records (default: True)
      --update-existing   Update existing records too
      --clear             Delete all Supabase data before export
      --sort {name,date,organizer,registrations,participants}
    
    WHAT IT DOES:
      1. Connects to Supabase PostgreSQL
      2. Fetches existing URLs (if --new-only)
      3. Filters out already-exported records
      4. Exports only new data
      5. Shows progress and summary
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-d', '--destination',
            type=str,
            choices=['unstop', 'devfolio'],
            default='unstop',
            help='Export destination: unstop or devfolio (default: unstop)',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data in Supabase before exporting',
        )
        parser.add_argument(
            '--sort',
            type=str,
            choices=['name', 'date', 'organizer', 'registrations', 'participants'],
            default='name',
            help='Sort order for export (default: name - alphabetically)',
        )
        parser.add_argument(
            '--new-only',
            action='store_true',
            default=True,
            help='Only export new records not in Supabase (default: True)',
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing records in Supabase (overrides --new-only)',
        )

    def handle(self, *args, **options):
        # Supabase connection details
        HOST = "db.rxdloipxqvjldsftitcn.supabase.co"
        PORT = "5432"
        DBNAME = "postgres"
        USER = "postgres"
        PASSWORD = os.getenv("SUPABASE_PASSWORD")
        
        destination = options['destination']
        new_only = options['new_only'] and not options['update_existing']

        if not PASSWORD:
            self.stdout.write(self.style.ERROR('SUPABASE_PASSWORD not found in .env file'))
            return

        # Determine which model and table to use
        if destination == 'devfolio':
            Model = DevfolioHackathon
            table_name = 'devfolio'
            self.stdout.write(self.style.SUCCESS(f'📋 Exporting Devfolio hackathons to "{table_name}" table'))
        else:  # unstop
            Model = Hackathon
            table_name = 'Unstop'
            self.stdout.write(self.style.SUCCESS(f'📋 Exporting Unstop hackathons to "{table_name}" table'))

        try:
            # Connect to Supabase
            self.stdout.write('🔌 Connecting to Supabase...')
            connection = psycopg2.connect(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                dbname=DBNAME
            )
            cursor = connection.cursor()
            self.stdout.write(self.style.SUCCESS('✅ Connected to Supabase!'))

            # Create table if not exists based on destination
            if destination == 'devfolio':
                create_table_query = """
                CREATE TABLE IF NOT EXISTS public.devfolio (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    url VARCHAR(500) UNIQUE NOT NULL,
                    organizer TEXT,
                    status VARCHAR(50),
                    participants_count VARCHAR(100),
                    projects_count VARCHAR(100),
                    about_content TEXT,
                    start_date TIMESTAMP WITH TIME ZONE,
                    end_date TIMESTAMP WITH TIME ZONE,
                    location TEXT,
                    organizer_contact TEXT,
                    important_dates TEXT,
                    official_website TEXT,
                    scraped_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                );
                """
            else:  # unstop
                create_table_query = """
                CREATE TABLE IF NOT EXISTS Unstop (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(500) NOT NULL,
                    url VARCHAR(500) UNIQUE NOT NULL,
                    organizer VARCHAR(500),
                    registered_count VARCHAR(100),
                    registration_count VARCHAR(100),
                    impression_count VARCHAR(100),
                    about_content TEXT,
                    organizer_contact TEXT,
                    important_dates TEXT,
                    official_website TEXT,
                    scraped_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                );
                """
            
            cursor.execute(create_table_query)
            connection.commit()
            self.stdout.write(self.style.SUCCESS(f'✅ Table "{table_name}" ready'))

            # Clear existing data if requested
            if options['clear']:
                cursor.execute(f"DELETE FROM {table_name};")
                connection.commit()
                self.stdout.write(self.style.WARNING(f'🗑️  Cleared existing data from {table_name} table'))
            
            # Get existing URLs from Supabase if new_only mode
            existing_urls = set()
            if new_only:
                self.stdout.write('🔍 Fetching existing URLs from Supabase...')
                cursor.execute(f"SELECT url FROM {table_name};")
                existing_urls = {row[0] for row in cursor.fetchall()}
                self.stdout.write(self.style.SUCCESS(f'✅ Found {len(existing_urls)} existing records in Supabase'))

            # Fetch all hackathons from SQLite with sorting
            sort_option = options['sort']
            
            if sort_option == 'name':
                hackathons = Model.objects.all().order_by('name')
                sort_desc = "alphabetically by name"
            elif sort_option == 'organizer':
                hackathons = Model.objects.all().order_by('organizer', 'name')
                sort_desc = "by organizer"
            elif sort_option == 'registrations' and destination == 'unstop':
                hackathons = Model.objects.all().order_by('-scraped_at')
                hackathons_list = list(hackathons)
                hackathons_list.sort(key=lambda x: int(x.registration_count or x.registered_count or '0') if (x.registration_count or x.registered_count or '0').replace(',', '').isdigit() else 0, reverse=True)
                hackathons = hackathons_list
                sort_desc = "by registration count (highest first)"
            elif sort_option == 'participants' and destination == 'devfolio':
                hackathons = Model.objects.all()
                hackathons_list = list(hackathons)
                hackathons_list.sort(key=lambda x: int(x.participants_count or '0') if (x.participants_count or '0').replace(',', '').isdigit() else 0, reverse=True)
                hackathons = hackathons_list
                sort_desc = "by participants count (highest first)"
            else:  # date (default)
                hackathons = Model.objects.all().order_by('-scraped_at')
                sort_desc = "by date (most recent first)"
            
            if not isinstance(hackathons, list):
                total = hackathons.count()
            else:
                total = len(hackathons)
            
            # Filter out existing URLs if new_only mode
            if new_only and existing_urls:
                if isinstance(hackathons, list):
                    hackathons = [h for h in hackathons if h.url not in existing_urls]
                else:
                    hackathons = hackathons.exclude(url__in=existing_urls)
                
                if not isinstance(hackathons, list):
                    new_count = hackathons.count()
                else:
                    new_count = len(hackathons)
                
                self.stdout.write(self.style.SUCCESS(f'📊 Found {total} total records'))
                self.stdout.write(self.style.SUCCESS(f'📊 After filtering: {new_count} new records to export (sorted {sort_desc})'))
                total = new_count
            else:
                self.stdout.write(f'📊 Found {total} records to export (sorted {sort_desc})')

            if total == 0:
                self.stdout.write(self.style.SUCCESS('✓ No new records to export. Database is up to date!'))
                cursor.close()
                connection.close()
                return

            # Export based on destination
            if destination == 'devfolio':
                inserted, skipped = self._export_devfolio(cursor, connection, hackathons, new_only, total)
            else:
                inserted, skipped = self._export_unstop(cursor, connection, hackathons, new_only, total)
            
            # Summary
            self.stdout.write(self.style.SUCCESS(f'\n✅ Export completed!'))
            if new_only:
                self.stdout.write(self.style.SUCCESS(f'  📈 New records added: {inserted}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  📈 Inserted/Updated: {inserted}'))
            if skipped > 0:
                self.stdout.write(self.style.WARNING(f'  ⚠️  Skipped (errors): {skipped}'))
            
            # Show total records in Supabase
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(f'  📊 Total in Supabase: {count}'))

            cursor.close()
            connection.close()
            self.stdout.write(self.style.SUCCESS('\n🔌 Connection closed.'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Failed to export: {e}'))
            import traceback
            traceback.print_exc()

    def _export_unstop(self, cursor, connection, hackathons, new_only, total):
        """Export Unstop hackathons"""
        inserted = 0
        skipped = 0
        
        if new_only:
            insert_query = """
            INSERT INTO Unstop (
                name, url, organizer, registered_count, registration_count,
                impression_count, about_content, organizer_contact,
                important_dates, official_website, scraped_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING;
            """
        else:
            insert_query = """
            INSERT INTO Unstop (
                name, url, organizer, registered_count, registration_count,
                impression_count, about_content, organizer_contact,
                important_dates, official_website, scraped_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
                name = EXCLUDED.name,
                organizer = EXCLUDED.organizer,
                registered_count = EXCLUDED.registered_count,
                registration_count = EXCLUDED.registration_count,
                impression_count = EXCLUDED.impression_count,
                about_content = EXCLUDED.about_content,
                organizer_contact = EXCLUDED.organizer_contact,
                important_dates = EXCLUDED.important_dates,
                official_website = EXCLUDED.official_website,
                updated_at = EXCLUDED.updated_at;
            """

        for hackathon in hackathons:
            try:
                name = (hackathon.name or '')[:500]
                organizer = (hackathon.organizer or '')[:500]
                registered_count = (hackathon.registered_count or '')[:100]
                registration_count = (hackathon.registration_count or '')[:100]
                impression_count = (hackathon.impression_count or '')[:100]
                url = (hackathon.url or '')[:500]
                
                cursor.execute(insert_query, (
                    name, url, organizer, registered_count, registration_count,
                    impression_count, hackathon.about_content, hackathon.organizer_contact,
                    hackathon.important_dates, hackathon.official_website,
                    hackathon.scraped_at, hackathon.updated_at,
                ))
                connection.commit()
                inserted += 1
                
                if inserted % 10 == 0:
                    self.stdout.write(f'⏳ Progress: {inserted}/{total}', ending='\r')
                    self.stdout.flush()
                    
            except Exception as e:
                connection.rollback()
                skipped += 1
                error_msg = str(e).split('\n')[0]
                self.stdout.write(self.style.WARNING(f'⚠️  Skipped: {hackathon.name[:50]} - {error_msg}'))
        
        return inserted, skipped

    def _export_devfolio(self, cursor, connection, hackathons, new_only, total):
        """Export Devfolio hackathons"""
        inserted = 0
        skipped = 0
        
        if new_only:
            insert_query = """
            INSERT INTO devfolio (
                name, url, organizer, status, participants_count, projects_count,
                about_content, start_date, end_date, location,
                organizer_contact, important_dates, official_website,
                scraped_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO NOTHING;
            """
        else:
            insert_query = """
            INSERT INTO devfolio (
                name, url, organizer, status, participants_count, projects_count,
                about_content, start_date, end_date, location,
                organizer_contact, important_dates, official_website,
                scraped_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE SET
                name = EXCLUDED.name,
                organizer = EXCLUDED.organizer,
                status = EXCLUDED.status,
                participants_count = EXCLUDED.participants_count,
                projects_count = EXCLUDED.projects_count,
                about_content = EXCLUDED.about_content,
                start_date = EXCLUDED.start_date,
                end_date = EXCLUDED.end_date,
                location = EXCLUDED.location,
                organizer_contact = EXCLUDED.organizer_contact,
                important_dates = EXCLUDED.important_dates,
                official_website = EXCLUDED.official_website,
                updated_at = EXCLUDED.updated_at;
            """

        for hackathon in hackathons:
            try:
                cursor.execute(insert_query, (
                    hackathon.name, hackathon.url, hackathon.organizer,
                    hackathon.status, hackathon.participants_count, hackathon.projects_count,
                    hackathon.about_content, hackathon.start_date, hackathon.end_date,
                    hackathon.location, hackathon.organizer_contact,
                    hackathon.important_dates, hackathon.official_website,
                    hackathon.scraped_at, hackathon.updated_at,
                ))
                connection.commit()
                inserted += 1
                
                if inserted % 10 == 0:
                    self.stdout.write(f'⏳ Progress: {inserted}/{total}', ending='\r')
                    self.stdout.flush()
                    
            except Exception as e:
                connection.rollback()
                skipped += 1
                error_msg = str(e).split('\n')[0]
                self.stdout.write(self.style.WARNING(f'⚠️  Skipped: {hackathon.name[:50]} - {error_msg}'))
        
        return inserted, skipped
