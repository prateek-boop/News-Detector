import psycopg2
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
import os
import secrets
import string

load_dotenv()


class Command(BaseCommand):
    help = 'Setup Row Level Security and create read-only user for Supabase'

    def add_arguments(self, parser):
        parser.add_argument(
            '--readonly-password',
            type=str,
            help='Password for read-only user (auto-generated if not provided)',
        )

    def handle(self, *args, **options):
        # Admin connection details
        HOST = os.getenv("SUPABASE_HOST", "db.rxdloipxqvjldsftitcn.supabase.co")
        PORT = os.getenv("SUPABASE_PORT", "5432")
        DBNAME = os.getenv("SUPABASE_DBNAME", "postgres")
        USER = os.getenv("SUPABASE_USER", "postgres")
        PASSWORD = os.getenv("SUPABASE_PASSWORD")

        if not PASSWORD:
            self.stdout.write(self.style.ERROR('SUPABASE_PASSWORD not found in .env file'))
            return

        # Generate or use provided password for read-only user
        readonly_password = options.get('readonly_password')
        if not readonly_password:
            # Generate secure random password
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            readonly_password = ''.join(secrets.choice(alphabet) for _ in range(20))
            self.stdout.write(self.style.WARNING(f'Generated password: {readonly_password}'))
            self.stdout.write(self.style.WARNING('Save this password securely!'))

        readonly_user = os.getenv("SUPABASE_READONLY_USER", "unstop_reader")

        try:
            # Connect to Supabase as admin
            self.stdout.write('Connecting to Supabase as admin...')
            connection = psycopg2.connect(
                user=USER,
                password=PASSWORD,
                host=HOST,
                port=PORT,
                dbname=DBNAME
            )
            connection.autocommit = True
            cursor = connection.cursor()
            self.stdout.write(self.style.SUCCESS('Connected!'))

            # Step 1: Create read-only user if not exists
            self.stdout.write('\n1. Creating read-only user...')
            try:
                cursor.execute(f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '{readonly_user}') THEN
                            CREATE USER {readonly_user} WITH PASSWORD '{readonly_password}';
                        ELSE
                            ALTER USER {readonly_user} WITH PASSWORD '{readonly_password}';
                        END IF;
                    END
                    $$;
                """)
                self.stdout.write(self.style.SUCCESS(f'  ✓ User "{readonly_user}" ready'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  User creation note: {e}'))

            # Step 2: Grant connect privileges
            self.stdout.write('\n2. Setting up permissions...')
            cursor.execute(f"GRANT CONNECT ON DATABASE {DBNAME} TO {readonly_user};")
            cursor.execute(f"GRANT USAGE ON SCHEMA public TO {readonly_user};")
            cursor.execute(f"GRANT SELECT ON Unstop TO {readonly_user};")
            self.stdout.write(self.style.SUCCESS('  ✓ Read-only permissions granted'))

            # Step 3: Enable Row Level Security
            self.stdout.write('\n3. Enabling Row Level Security...')
            cursor.execute("ALTER TABLE Unstop ENABLE ROW LEVEL SECURITY;")
            self.stdout.write(self.style.SUCCESS('  ✓ RLS enabled on Unstop table'))

            # Step 4: Drop existing policies if they exist
            self.stdout.write('\n4. Setting up RLS policies...')
            cursor.execute("""
                DROP POLICY IF EXISTS "Admin full access" ON Unstop;
                DROP POLICY IF EXISTS "Authenticated read access" ON Unstop;
            """)

            # Step 5: Create policies
            # Policy 1: Admin (postgres) has full access
            cursor.execute(f"""
                CREATE POLICY "Admin full access" ON Unstop
                FOR ALL
                TO {USER}
                USING (true)
                WITH CHECK (true);
            """)
            
            # Policy 2: Read-only user can only SELECT
            cursor.execute(f"""
                CREATE POLICY "Authenticated read access" ON Unstop
                FOR SELECT
                TO {readonly_user}
                USING (true);
            """)
            self.stdout.write(self.style.SUCCESS('  ✓ RLS policies created'))

            # Step 6: Revoke public access
            self.stdout.write('\n5. Securing table...')
            cursor.execute("REVOKE ALL ON Unstop FROM PUBLIC;")
            self.stdout.write(self.style.SUCCESS('  ✓ Public access revoked'))

            # Test the setup
            self.stdout.write('\n6. Testing configuration...')
            cursor.execute("SELECT COUNT(*) FROM Unstop;")
            count = cursor.fetchone()[0]
            self.stdout.write(self.style.SUCCESS(f'  ✓ Admin can read: {count} records'))

            cursor.close()
            connection.close()

            # Summary
            self.stdout.write(self.style.SUCCESS('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('✓ Security setup completed!'))
            self.stdout.write(self.style.SUCCESS('='*60))
            self.stdout.write('\nCredentials for read-only access:')
            self.stdout.write(f'  Host: {HOST}')
            self.stdout.write(f'  Port: {PORT}')
            self.stdout.write(f'  Database: {DBNAME}')
            self.stdout.write(f'  Username: {readonly_user}')
            self.stdout.write(f'  Password: {readonly_password}')
            self.stdout.write('\nUpdate your .env file with:')
            self.stdout.write(f'SUPABASE_READONLY_USER={readonly_user}')
            self.stdout.write(f'SUPABASE_READONLY_PASSWORD={readonly_password}')
            self.stdout.write('\nSecurity features enabled:')
            self.stdout.write('  • Row Level Security (RLS) enabled')
            self.stdout.write('  • Admin has full access (read/write/delete)')
            self.stdout.write('  • Read-only user has SELECT access only')
            self.stdout.write('  • Public access revoked')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nFailed to setup security: {e}'))
