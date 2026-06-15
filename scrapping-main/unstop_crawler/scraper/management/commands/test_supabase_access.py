import psycopg2
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
import os

load_dotenv()


class Command(BaseCommand):
    help = 'Test Supabase access with read-only credentials'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin',
            action='store_true',
            help='Test with admin credentials instead of read-only',
        )

    def handle(self, *args, **options):
        HOST = os.getenv("SUPABASE_HOST", "db.rxdloipxqvjldsftitcn.supabase.co")
        PORT = os.getenv("SUPABASE_PORT", "5432")
        DBNAME = os.getenv("SUPABASE_DBNAME", "postgres")

        if options['admin']:
            USER = os.getenv("SUPABASE_USER", "postgres")
            PASSWORD = os.getenv("SUPABASE_PASSWORD")
            user_type = "ADMIN"
        else:
            USER = os.getenv("SUPABASE_READONLY_USER", "unstop_reader")
            PASSWORD = os.getenv("SUPABASE_READONLY_PASSWORD")
            user_type = "READ-ONLY"

        if not PASSWORD:
            self.stdout.write(self.style.ERROR(f'Password not found in .env file'))
            return

        try:
            self.stdout.write(f'Testing {user_type} access...')
            self.stdout.write(f'User: {USER}')
            
            connection = psycopg2.connect(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                dbname=DBNAME
            )
            cursor = connection.cursor()
            self.stdout.write(self.style.SUCCESS('✓ Connected successfully!'))

            # Test SELECT
            self.stdout.write('\nTesting SELECT query...')
            cursor.execute("SELECT COUNT(*) FROM Unstop;")
            count = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(f'✓ Can read {count} records'))

            # Show sample records
            cursor.execute("SELECT name, organizer FROM Unstop LIMIT 3;")
            records = cursor.fetchall()
            self.stdout.write('\nSample records:')
            for i, (name, organizer) in enumerate(records, 1):
                self.stdout.write(f'  {i}. {name} (by {organizer})')

            if not options['admin']:
                # Test INSERT (should fail for read-only)
                self.stdout.write('\nTesting INSERT (should fail)...')
                try:
                    cursor.execute("""
                        INSERT INTO Unstop (name, url, scraped_at, updated_at)
                        VALUES ('Test', 'http://test.com', NOW(), NOW());
                    """)
                    connection.commit()
                    self.stdout.write(self.style.ERROR('✗ INSERT succeeded (security issue!)'))
                except Exception as e:
                    self.stdout.write(self.style.SUCCESS(f'✓ INSERT blocked: {str(e)[:50]}...'))

                # Test DELETE (should fail for read-only)
                self.stdout.write('\nTesting DELETE (should fail)...')
                try:
                    cursor.execute("DELETE FROM Unstop WHERE id = 1;")
                    connection.commit()
                    self.stdout.write(self.style.ERROR('✗ DELETE succeeded (security issue!)'))
                except Exception as e:
                    self.stdout.write(self.style.SUCCESS(f'✓ DELETE blocked: {str(e)[:50]}...'))

            cursor.close()
            connection.close()
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ {user_type} access working correctly!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Failed: {e}'))
