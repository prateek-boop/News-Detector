from django.core.management.base import BaseCommand
from django.core.management import get_commands


class Command(BaseCommand):
    help = """
    ===============================================================================
    UNSTOP CRAWLER - COMPREHENSIVE HELP GUIDE
    ===============================================================================
    
    This tool scrapes hackathons and competitions from Unstop, Devfolio, and Devpost,
    stores them in SQLite/Supabase, and exports to JSON/CSV.
    
    
    📋 AVAILABLE COMMANDS:
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🔍 URL COLLECTION COMMANDS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    get_all_urls          Get all Unstop hackathon & competition URLs
                          python manage.py get_all_urls
                          python manage.py get_all_urls --output my_urls.txt
    
    get_devfolio_urls     Get all Devfolio hackathon URLs
                          python manage.py get_devfolio_urls
                          python manage.py get_devfolio_urls --status past
                          python manage.py get_devfolio_urls --status all
    
    get_devpost_urls_api  Get all Devpost hackathon URLs (RECOMMENDED)
                          python manage.py get_devpost_urls_api
                          python manage.py get_devpost_urls_api --output devpost_all.txt
                          python manage.py get_devpost_urls_api --status open
    
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🌐 SCRAPING COMMANDS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    scrape_unstop         Scrape Unstop hackathons
                          python manage.py scrape_unstop --limit 10
                          python manage.py scrape_unstop --from-file urls.txt
                          python manage.py scrape_unstop --skip-existing
    
    scrape_competitions   Scrape Unstop competitions
                          python manage.py scrape_competitions --limit 10
                          python manage.py scrape_competitions --from-file urls.txt
    
    scrape_devfolio       Scrape Devfolio hackathons
                          python manage.py scrape_devfolio --status open
                          python manage.py scrape_devfolio --status all --limit 50
                          python manage.py scrape_devfolio --from-file urls.txt
    
    scrape_devpost        Scrape Devpost hackathons (OPTIMIZED - essential data only)
                          python manage.py scrape_devpost --from-file devpost_all.txt --headless
                          python manage.py scrape_devpost --url <URL> --headless
                          python manage.py scrape_devpost --limit 10 --headless
    
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🔄 UPDATE COMMANDS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    update_unstop         Update specific Unstop hackathon/competition
                          python manage.py update_unstop --url <URL>
                          python manage.py update_unstop --outdated-only
                          python manage.py update_unstop --update-contacts
    
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📤 EXPORT COMMANDS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    export_hackathons     Export Unstop hackathons to JSON/CSV
                          python manage.py export_hackathons
    
    export_competitions   Export Unstop competitions to JSON/CSV
                          python manage.py export_competitions
    
    export_devfolio       Export Devfolio hackathons to JSON/CSV
                          python manage.py export_devfolio
    
    export_devpost        Export Devpost hackathons to JSON/CSV
                          python manage.py export_devpost --format json
                          python manage.py export_devpost --format csv --sort participants
    
    export_to_supabase    Export Unstop data to Supabase (sorted alphabetically)
                          python manage.py export_to_supabase
                          python manage.py export_to_supabase --table Unstop
                          python manage.py export_to_supabase --table Devfolio
    
    export_devfolio_to_supabase  Export Devfolio to Supabase (sorted by name)
                                 python manage.py export_devfolio_to_supabase
                                 python manage.py export_devfolio_to_supabase --clear
    
    export_devpost_to_supabase   Export Devpost to Supabase (sorted by name)
                                 python manage.py export_devpost_to_supabase
                                 python manage.py export_devpost_to_supabase --clear
                                 python manage.py export_devpost_to_supabase --sort participants
    
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    🔧 UTILITY COMMANDS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    setup_supabase_security    Setup Supabase RLS policies
                               python manage.py setup_supabase_security
    
    test_supabase_access       Test Supabase connection
                               python manage.py test_supabase_access
    
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📖 DETAILED HELP
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    For detailed help on any command, use:
        python manage.py <command> --help
    
    Examples:
        python manage.py scrape_unstop --help
        python manage.py scrape_devpost --help
        python manage.py export_to_supabase --help
        python manage.py get_devpost_urls_api --help
    
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    💡 COMMON WORKFLOWS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    1. Initial Setup & Full Scrape (Unstop):
       python manage.py get_all_urls
       python manage.py scrape_unstop --from-file hackathon_urls.txt
       python manage.py scrape_competitions --from-file hackathon_urls.txt
       python manage.py export_to_supabase
    
    2. Scrape Devfolio:
       python manage.py get_devfolio_urls --status all
       python manage.py scrape_devfolio --from-file devfolio_all_urls.txt
       python manage.py export_devfolio_to_supabase
    
    3. Scrape Devpost (RECOMMENDED WORKFLOW):
       python manage.py get_devpost_urls_api --output devpost_all.txt
       python manage.py scrape_devpost --from-file devpost_all.txt --headless
       python manage.py export_devpost_to_supabase
    
    4. Update Outdated Data:
       python manage.py update_unstop --outdated-only
    
    5. Quick Test (Limit 10):
       python manage.py scrape_unstop --limit 10
       python manage.py scrape_devfolio --status open --limit 10
       python manage.py scrape_devpost --limit 10 --headless
    
    
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    📊 EXTRACTED DATA FIELDS
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    Unstop Hackathons/Competitions:
      • Name, URL, Organizer
      • Registration count, Impression count
      • About content, Important dates
      • Organizer contact (excluding Unstop support)
      • Official website, Prizes
      • Scraped/Updated timestamps
    
    Devfolio Hackathons:
      • Name, URL, Organizer, Status
      • Participants count, Projects count
      • About content, Dates (start/end)
      • Location, Mode (online/offline/hybrid)
      • Prizes, Themes, Contact info
      • Official website, Social links
    
    Devpost Hackathons (OPTIMIZED):
      • ID, Name, URL, Organizer
      • Participants count
      • About content
      • Organizer contact
      • Sponsors
      • Scraped/Updated timestamps
    
    
    ===============================================================================
    """

    def handle(self, *args, **options):
        self.stdout.write(self.help)
