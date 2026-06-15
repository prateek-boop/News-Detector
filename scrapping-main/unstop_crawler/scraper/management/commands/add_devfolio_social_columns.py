import psycopg2
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
import os

load_dotenv()


class Command(BaseCommand):
    help = """
    Add social media columns to Devfolio table in Supabase.
    
    This command alters the Devfolio table to add columns for:
    - telegram_link
    - discord_link
    - linkedin_link
    - twitter_link
    
    USAGE:
    
      python manage.py add_devfolio_social_columns
    
    EXAMPLES:
    
      # Add social media columns to Devfolio table
      python manage.py add_devfolio_social_columns
      
      # Check if columns need to be added
      python manage.py add_devfolio_social_columns --check-only
    
    OPTIONS:
      --check-only     Only check if columns exist, don't add them
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='Only check if columns exist without adding them',
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

            # Check if Devfolio table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'Devfolio'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                self.stdout.write(self.style.ERROR('Devfolio table does not exist. Run export_devfolio_to_supabase first.'))
                return

            # Check which columns exist
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'Devfolio';
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            social_columns = {
                'telegram_link': 'VARCHAR(500)',
                'discord_link': 'VARCHAR(500)',
                'linkedin_link': 'VARCHAR(500)',
                'twitter_link': 'VARCHAR(500)',
            }
            
            columns_to_add = []
            for col_name, col_type in social_columns.items():
                if col_name not in existing_columns:
                    columns_to_add.append((col_name, col_type))
            
            if options['check_only']:
                if columns_to_add:
                    self.stdout.write(self.style.WARNING(f'Missing columns: {[c[0] for c in columns_to_add]}'))
                else:
                    self.stdout.write(self.style.SUCCESS('All social media columns already exist!'))
                return
            
            if not columns_to_add:
                self.stdout.write(self.style.SUCCESS('All social media columns already exist!'))
                return
            
            # Add missing columns
            self.stdout.write(f'Adding {len(columns_to_add)} columns...')
            for col_name, col_type in columns_to_add:
                try:
                    alter_query = f"""
                    ALTER TABLE "Devfolio"
                    ADD COLUMN IF NOT EXISTS "{col_name}" {col_type};
                    """
                    cursor.execute(alter_query)
                    connection.commit()
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Added: {col_name}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Failed to add {col_name}: {str(e)}'))
                    connection.rollback()
            
            # Verify columns were added
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'Devfolio'
                AND column_name IN ('telegram_link', 'discord_link', 'linkedin_link', 'twitter_link');
            """)
            added_columns = [row[0] for row in cursor.fetchall()]
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Schema update completed!'))
            self.stdout.write(self.style.SUCCESS(f'  Social media columns: {len(added_columns)}/4'))
            
            cursor.close()
            connection.close()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            import traceback
            traceback.print_exc()
