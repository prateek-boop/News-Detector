from django.core.management.base import BaseCommand
from django.core.management import get_commands, load_command_class


class Command(BaseCommand):
    help = """
    Display help for all available Unstop Crawler commands.
    
    This shows a comprehensive list of all scraping, export, and utility commands.
    For detailed help on any command, use: python manage.py <command> --help
    
    USAGE:
        python manage.py help
        python manage.py <command> --help    # For detailed command help
    """

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("\n" + "="*70))
        self.stdout.write(self.style.SUCCESS("  UNSTOP CRAWLER - Available Commands"))
        self.stdout.write(self.style.SUCCESS("="*70 + "\n"))
        
        custom_commands = {
            'scrape_unstop': 'Scrape hackathons from Unstop.com',
            'scrape_competitions': 'Scrape competitions from Unstop.com',
            'scrape_devfolio': 'Scrape hackathons from Devfolio.co',
            'scrape_devpost': 'Scrape hackathons from Devpost.com',
            'update_unstop': 'Update existing Unstop hackathon data',
            'get_all_urls': 'Extract all hackathon/competition URLs from Unstop',
            'get_devfolio_urls': 'Extract all hackathon URLs from Devfolio',
            'get_devpost_urls': 'Extract all hackathon URLs from Devpost (~12k)',
            'export_hackathons': 'Export hackathons to CSV/JSON',
            'export_competitions': 'Export competitions to CSV/JSON',
            'export_devfolio': 'Export Devfolio hackathons to CSV/JSON',
            'export_devpost': 'Export Devpost hackathons to JSON',
            'export_to_supabase': 'Export Unstop data to Supabase PostgreSQL',
            'export_devfolio_to_supabase': 'Export Devfolio data to Supabase',
            'setup_supabase_security': 'Setup RLS policies for Supabase',
            'test_supabase_access': 'Test Supabase connection',
        }
        
        # Scraping Commands
        self.stdout.write(self.style.WARNING("📥 SCRAPING COMMANDS:"))
        self.stdout.write("")
        for cmd in ['scrape_unstop', 'scrape_competitions', 'scrape_devfolio', 'scrape_devpost', 'get_all_urls', 'get_devfolio_urls', 'get_devpost_urls']:
            if cmd in custom_commands:
                self.stdout.write(f"  • {self.style.SUCCESS(cmd.ljust(25))} - {custom_commands[cmd]}")
        
        # Update Commands
        self.stdout.write(self.style.WARNING("\n🔄 UPDATE COMMANDS:"))
        self.stdout.write("")
        for cmd in ['update_unstop']:
            if cmd in custom_commands:
                self.stdout.write(f"  • {self.style.SUCCESS(cmd.ljust(25))} - {custom_commands[cmd]}")
        
        # Export Commands
        self.stdout.write(self.style.WARNING("\n📤 EXPORT COMMANDS:"))
        self.stdout.write("")
        for cmd in ['export_hackathons', 'export_competitions', 'export_devfolio', 'export_devpost', 'export_to_supabase', 'export_devfolio_to_supabase']:
            if cmd in custom_commands:
                self.stdout.write(f"  • {self.style.SUCCESS(cmd.ljust(25))} - {custom_commands[cmd]}")
        
        # Database Commands
        self.stdout.write(self.style.WARNING("\n💾 DATABASE COMMANDS:"))
        self.stdout.write("")
        for cmd in ['setup_supabase_security', 'test_supabase_access']:
            if cmd in custom_commands:
                self.stdout.write(f"  • {self.style.SUCCESS(cmd.ljust(25))} - {custom_commands[cmd]}")
        
        # Usage examples
        self.stdout.write(self.style.WARNING("\n📝 QUICK START EXAMPLES:"))
        self.stdout.write("")
        self.stdout.write("  # Get all URLs from Unstop")
        self.stdout.write(f"  {self.style.SUCCESS('python manage.py get_all_urls --output unstop_urls.txt')}")
        self.stdout.write("")
        self.stdout.write("  # Scrape hackathons from Unstop")
        self.stdout.write(f"  {self.style.SUCCESS('python manage.py scrape_unstop --from-file unstop_urls.txt --headless')}")
        self.stdout.write("")
        self.stdout.write("  # Update outdated hackathons")
        self.stdout.write(f"  {self.style.SUCCESS('python manage.py update_unstop --outdated-only')}")
        self.stdout.write("")
        self.stdout.write("  # Get all Devpost URLs")
        self.stdout.write(f"  {self.style.SUCCESS('python manage.py get_devpost_urls --output devpost_urls.txt --headless')}")
        self.stdout.write("")
        self.stdout.write("  # Scrape from Devpost")
        self.stdout.write(f"  {self.style.SUCCESS('python manage.py scrape_devpost --from-file devpost_urls.txt --headless')}")
        self.stdout.write("")
        self.stdout.write("  # Export to Supabase")
        self.stdout.write(f"  {self.style.SUCCESS('python manage.py export_to_supabase')}")
        self.stdout.write("")
        
        # Get detailed help
        self.stdout.write(self.style.WARNING("ℹ️  GET DETAILED HELP:"))
        self.stdout.write("")
        self.stdout.write("  For detailed options and examples for any command:")
        self.stdout.write(f"  {self.style.SUCCESS('python manage.py <command> --help')}")
        self.stdout.write("")
        self.stdout.write("  Example:")
        self.stdout.write(f"  {self.style.SUCCESS('python manage.py scrape_unstop --help')}")
        
        self.stdout.write(self.style.SUCCESS("\n" + "="*70 + "\n"))
