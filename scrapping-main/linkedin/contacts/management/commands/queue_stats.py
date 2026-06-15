from django.core.management.base import BaseCommand
from contacts.models import Post, Profile, Contact, ScrapingSession

class Command(BaseCommand):
    help = 'Show scraping queue statistics and status'

    def handle(self, *args, **options):
        # Posts statistics
        pending_posts = Post.objects.filter(scraped=False).count()
        scraped_posts = Post.objects.filter(scraped=True).count()
        total_posts = Post.objects.count()
        
        # Profile statistics
        pending_profiles = Profile.objects.filter(activity_scraped=False).count()
        scraped_profiles = Profile.objects.filter(activity_scraped=True).count()
        total_profiles = Profile.objects.count()
        
        # Contact statistics
        total_emails = Contact.objects.count()
        
        # Session statistics
        total_sessions = ScrapingSession.objects.count()
        running_sessions = ScrapingSession.objects.filter(status='running').count()
        
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("SCRAPING QUEUE STATISTICS"))
        self.stdout.write("="*70)
        
        self.stdout.write("\nPOSTS:")
        self.stdout.write(f"  Pending:       {pending_posts:,}")
        self.stdout.write(f"  Scraped:       {scraped_posts:,}")
        self.stdout.write(f"  Total:         {total_posts:,}")
        
        self.stdout.write("\nPROFILES:")
        self.stdout.write(f"  Pending:       {pending_profiles:,}")
        self.stdout.write(f"  Scraped:       {scraped_profiles:,}")
        self.stdout.write(f"  Total:         {total_profiles:,}")
        
        self.stdout.write("\nEMAILS:")
        self.stdout.write(f"  Total:         {total_emails:,}")
        
        self.stdout.write("\nSESSIONS:")
        self.stdout.write(f"  Total:         {total_sessions}")
        self.stdout.write(f"  Running:       {running_sessions}")
        
        # Show top pending posts by comment count
        top_posts = Post.objects.filter(scraped=False).order_by('-comment_count')[:10]
        if top_posts.exists():
            self.stdout.write("\nTOP PENDING POSTS (by comment count):")
            for i, post in enumerate(top_posts, 1):
                comment_str = f"{post.comment_count}" if post.comment_count else "Unknown"
                url_short = post.post_url[:80] + "..." if len(post.post_url) > 80 else post.post_url
                self.stdout.write(f"  {i:2d}. {comment_str:>6s} comments - {url_short}")
        
        # Show recent sessions
        recent_sessions = ScrapingSession.objects.all()[:5]
        if recent_sessions.exists():
            self.stdout.write("\nRECENT SESSIONS:")
            for session in recent_sessions:
                status_color = self.style.SUCCESS if session.status == 'completed' else self.style.WARNING
                self.stdout.write(
                    f"  #{session.id} - {status_color(session.status.upper())} - "
                    f"Depth {session.depth_level} - "
                    f"{session.posts_scraped} posts - "
                    f"{session.profiles_scraped} profiles - "
                    f"{session.emails_collected} emails"
                )
        
        # Show discovery statistics
        profiles_with_discoveries = Profile.objects.filter(posts_discovered_count__gt=0).count()
        total_discoveries = sum(Profile.objects.values_list('posts_discovered_count', flat=True))
        
        if profiles_with_discoveries > 0:
            self.stdout.write("\nDISCOVERY STATISTICS:")
            self.stdout.write(f"  Profiles with discoveries: {profiles_with_discoveries:,}")
            self.stdout.write(f"  Total posts discovered:    {total_discoveries:,}")
            avg_per_profile = total_discoveries / profiles_with_discoveries if profiles_with_discoveries > 0 else 0
            self.stdout.write(f"  Average per profile:       {avg_per_profile:.1f}")
        
        self.stdout.write("\n" + "="*70)
