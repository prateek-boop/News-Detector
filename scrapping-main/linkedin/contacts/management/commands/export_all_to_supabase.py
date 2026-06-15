import os
import psycopg2
from django.core.management.base import BaseCommand
from django.core.management import call_command
from contacts.models import Contact, Profile
from dotenv import load_dotenv

load_dotenv()

class Command(BaseCommand):
    help = 'Export all data (contacts + profiles) to Supabase in one command'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be exported without actually exporting',
        )
        parser.add_argument(
            '--skip-contacts',
            action='store_true',
            help='Skip contact export, only export profiles',
        )
        parser.add_argument(
            '--skip-profiles',
            action='store_true',
            help='Skip profile export, only export contacts',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        skip_contacts = options['skip_contacts']
        skip_profiles = options['skip_profiles']
        
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("Supabase Complete Export"))
        self.stdout.write("="*70)
        
        # Validate Supabase configuration
        supabase_config = {
            'host': os.getenv('SUPABASE_HOST'),
            'port': os.getenv('SUPABASE_PORT'),
            'dbname': os.getenv('SUPABASE_DBNAME'),
            'user': os.getenv('SUPABASE_USER'),
            'password': os.getenv('SUPABASE_PASSWORD')
        }
        
        if not all(supabase_config.values()):
            self.stdout.write(self.style.ERROR('Missing Supabase configuration in .env file'))
            return
        
        # Get counts
        contact_count = Contact.objects.count()
        profile_count = Profile.objects.count()
        
        self.stdout.write(f"\nLocal Database:")
        self.stdout.write(f"  Contacts: {contact_count}")
        self.stdout.write(f"  Profiles: {profile_count}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN MODE - No data will be exported'))
        
        # Export contacts
        if not skip_contacts:
            self.stdout.write("\n" + "="*70)
            self.stdout.write("PART 1: Exporting Contacts")
            self.stdout.write("="*70)
            
            if contact_count == 0:
                self.stdout.write(self.style.WARNING('No contacts to export'))
            else:
                try:
                    call_command('export_to_supabase', dry_run=dry_run)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Contact export failed: {e}'))
        else:
            self.stdout.write("\nSkipping contact export")
        
        # Export profiles
        if not skip_profiles:
            self.stdout.write("\n" + "="*70)
            self.stdout.write("PART 2: Exporting Profiles")
            self.stdout.write("="*70)
            
            if profile_count == 0:
                self.stdout.write(self.style.WARNING('No profiles to export'))
            else:
                try:
                    call_command('export_profiles_to_supabase', dry_run=dry_run)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Profile export failed: {e}'))
        else:
            self.stdout.write("\nSkipping profile export")
        
        # Final summary
        if not dry_run:
            self.stdout.write("\n" + "="*70)
            self.stdout.write(self.style.SUCCESS("COMPLETE EXPORT SUMMARY"))
            self.stdout.write("="*70)
            
            try:
                # Connect to check Supabase counts
                conn = psycopg2.connect(**supabase_config)
                cursor = conn.cursor()
                
                # Count contacts in Supabase
                cursor.execute("SELECT COUNT(*) FROM linkedin")
                supabase_contacts = cursor.fetchone()[0]
                
                # Count profiles in Supabase
                cursor.execute("SELECT COUNT(*) FROM linkedin_profiles")
                supabase_profiles = cursor.fetchone()[0]
                
                cursor.close()
                conn.close()
                
                self.stdout.write(f"\nLocal Database:")
                self.stdout.write(f"  Contacts: {contact_count}")
                self.stdout.write(f"  Profiles: {profile_count}")
                
                self.stdout.write(f"\nSupabase Database:")
                self.stdout.write(f"  Contacts: {supabase_contacts}")
                self.stdout.write(f"  Profiles: {supabase_profiles}")
                
                # Show sync status
                contact_diff = contact_count - supabase_contacts
                profile_diff = profile_count - supabase_profiles
                
                if contact_diff == 0 and profile_diff == 0:
                    self.stdout.write(self.style.SUCCESS("\nAll data synced successfully!"))
                else:
                    if contact_diff > 0:
                        self.stdout.write(self.style.WARNING(f"\nWarning: {contact_diff} contacts not in Supabase"))
                    if profile_diff > 0:
                        self.stdout.write(self.style.WARNING(f"Warning: {profile_diff} profiles not in Supabase"))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'\nCould not verify Supabase counts: {e}'))
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("Export Complete!"))
        self.stdout.write("="*70)
