from django.core.management.base import BaseCommand
from contacts.models import Post, Profile, ScrapingSession

class Command(BaseCommand):
    help = 'Reset scraping queue flags for re-scraping'

    def add_arguments(self, parser):
        parser.add_argument(
            '--posts',
            action='store_true',
            help='Reset post scraped flags (allows re-scraping posts)'
        )
        parser.add_argument(
            '--profiles',
            action='store_true',
            help='Reset profile activity scraped flags (allows re-scraping activity)'
        )
        parser.add_argument(
            '--sessions',
            action='store_true',
            help='Delete all scraping sessions'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Reset everything (posts, profiles, sessions)'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm the reset operation'
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING("="*70))
            self.stdout.write(self.style.WARNING("RESET QUEUE - CONFIRMATION REQUIRED"))
            self.stdout.write(self.style.WARNING("="*70))
            self.stdout.write("\nThis will reset scraping flags, allowing data to be re-scraped.")
            self.stdout.write("Add --confirm flag to proceed.\n")
            self.stdout.write("Examples:")
            self.stdout.write("  python manage.py queue_reset --posts --confirm")
            self.stdout.write("  python manage.py queue_reset --profiles --confirm")
            self.stdout.write("  python manage.py queue_reset --all --confirm")
            self.stdout.write("\n" + "="*70)
            return
        
        reset_posts = options['posts'] or options['all']
        reset_profiles = options['profiles'] or options['all']
        reset_sessions = options['sessions'] or options['all']
        
        self.stdout.write("="*70)
        self.stdout.write(self.style.WARNING("RESETTING QUEUE FLAGS"))
        self.stdout.write("="*70 + "\n")
        
        if reset_posts:
            count = Post.objects.filter(scraped=True).update(
                scraped=False,
                scraped_at=None
            )
            self.stdout.write(f"Reset {count:,} posts (marked as unscraped)")
        
        if reset_profiles:
            count = Profile.objects.filter(activity_scraped=True).update(
                activity_scraped=False,
                activity_scraped_at=None,
                posts_discovered_count=0
            )
            self.stdout.write(f"Reset {count:,} profiles (marked activity as unscraped)")
        
        if reset_sessions:
            count = ScrapingSession.objects.count()
            ScrapingSession.objects.all().delete()
            self.stdout.write(f"Deleted {count} scraping sessions")
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("RESET COMPLETE"))
        self.stdout.write("="*70)
        
        # Show current stats
        self.stdout.write(f"\nCurrent queue status:")
        self.stdout.write(f"  Pending posts:    {Post.objects.filter(scraped=False).count():,}")
        self.stdout.write(f"  Pending profiles: {Profile.objects.filter(activity_scraped=False).count():,}")
        self.stdout.write(f"  Sessions:         {ScrapingSession.objects.count()}")
        self.stdout.write("")
