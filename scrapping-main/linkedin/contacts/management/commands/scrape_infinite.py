from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import timezone
from contacts.models import Post, Profile, Contact, ScrapingSession
from io import StringIO
import time

class Command(BaseCommand):
    help = 'Infinite scraping loop - posts → profiles → activity → new posts → repeat'

    def add_arguments(self, parser):
        parser.add_argument(
            '--seed-url',
            type=str,
            required=True,
            help='Initial post URL to start scraping'
        )
        parser.add_argument(
            '--max-depth',
            type=int,
            default=999,
            help='Maximum depth levels to scrape (default: 999)'
        )
        parser.add_argument(
            '--max-posts',
            type=int,
            default=999999,
            help='Maximum posts to scrape total (default: 999999)'
        )
        parser.add_argument(
            '--min-comments',
            type=int,
            default=100,
            help='Minimum comments required to queue post (default: 100)'
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=5,
            help='Delay between posts in seconds (default: 5)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of profiles to scrape activity per batch (default: 10)'
        )
        parser.add_argument(
            '--visible',
            action='store_true',
            help='Run browser in visible mode'
        )
        parser.add_argument(
            '--skip-activity',
            action='store_true',
            help='Skip profile activity scraping (only scrape seed posts)'
        )

    def handle(self, *args, **options):
        seed_url = options['seed_url']
        max_depth = options['max_depth']
        max_posts = options['max_posts']
        min_comments = options['min_comments']
        delay = options['delay']
        batch_size = options['batch_size']
        visible = options['visible']
        skip_activity = options['skip_activity']
        
        # Create scraping session
        session = ScrapingSession.objects.create(
            seed_url=seed_url,
            max_posts=max_posts,
            max_depth=max_depth,
            status='running'
        )
        
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("INFINITE LOOP SCRAPER"))
        self.stdout.write("="*70)
        self.stdout.write(f"Session ID: {session.id}")
        self.stdout.write(f"Seed URL: {seed_url}")
        self.stdout.write(f"Max depth: {max_depth}")
        self.stdout.write(f"Max posts: {max_posts}")
        self.stdout.write(f"Min comments: {min_comments}")
        self.stdout.write(f"Batch size: {batch_size}")
        self.stdout.write(f"Mode: {'VISIBLE' if visible else 'HEADLESS'}")
        self.stdout.write("="*70 + "\n")
        
        # Add seed URL to queue
        seed_post, created = Post.objects.get_or_create(
            post_url=seed_url,
            defaults={'comment_count': 9999}  # High priority
        )
        
        if created:
            self.stdout.write(f"Added seed post to queue")
        else:
            self.stdout.write(f"Seed post already in queue")
        
        depth = 0
        posts_scraped = 0
        
        try:
            while depth < max_depth and posts_scraped < max_posts:
                self.stdout.write(f"\n{'='*70}")
                self.stdout.write(f"DEPTH LEVEL: {depth + 1}")
                self.stdout.write(f"{'='*70}\n")
                
                # Step 1: Get pending posts to scrape
                pending_posts = Post.objects.filter(scraped=False).order_by('-comment_count')
                pending_count = pending_posts.count()
                
                if pending_count == 0:
                    self.stdout.write(self.style.WARNING("No more posts in queue. Scraping complete."))
                    break
                
                self.stdout.write(f"Posts in queue: {pending_count}")
                self.stdout.write(f"Scraping batch of posts...\n")
                
                # Step 2: Scrape posts to get profiles and emails
                batch_scraped = 0
                for post in pending_posts[:batch_size]:
                    if posts_scraped >= max_posts:
                        break
                    
                    self.stdout.write(f"\n[Post {posts_scraped + 1}/{max_posts}] {post.post_url}")
                    
                    try:
                        # Call scrape_all command
                        call_command(
                            'scrape_all',
                            url=post.post_url,
                            visible=visible,
                            stdout=StringIO()  # Suppress output
                        )
                        
                        # Mark post as scraped
                        post.scraped = True
                        post.scraped_at = timezone.now()
                        post.save()
                        
                        posts_scraped += 1
                        batch_scraped += 1
                        
                        # Update session
                        session.posts_scraped = posts_scraped
                        session.depth_level = depth + 1
                        session.profiles_scraped = Profile.objects.count()
                        session.emails_collected = Contact.objects.count()
                        session.save()
                        
                        self.stdout.write(self.style.SUCCESS("  Scraped successfully"))
                        
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  Error: {str(e)}"))
                        # Mark as scraped to avoid retrying
                        post.scraped = True
                        post.scraped_at = timezone.now()
                        post.save()
                        continue
                    
                    # Delay between posts
                    if delay > 0:
                        time.sleep(delay)
                
                # Show progress after batch
                profiles_count = Profile.objects.count()
                emails_count = Contact.objects.count()
                pending_count = Post.objects.filter(scraped=False).count()
                
                self.stdout.write(f"\n{'='*70}")
                self.stdout.write(f"BATCH COMPLETE")
                self.stdout.write(f"{'='*70}")
                self.stdout.write(f"Posts scraped this batch: {batch_scraped}")
                self.stdout.write(f"Total posts scraped: {posts_scraped}")
                self.stdout.write(f"Total profiles: {profiles_count}")
                self.stdout.write(f"Total emails: {emails_count}")
                self.stdout.write(f"Posts in queue: {pending_count}")
                
                # Step 3: Scrape profile activity to discover new posts
                if not skip_activity:
                    pending_profiles = Profile.objects.filter(activity_scraped=False).count()
                    
                    if pending_profiles > 0:
                        self.stdout.write(f"\n{'='*70}")
                        self.stdout.write(f"DISCOVERING NEW POSTS FROM PROFILES")
                        self.stdout.write(f"{'='*70}")
                        self.stdout.write(f"Pending profiles: {pending_profiles}")
                        self.stdout.write(f"Scraping {min(batch_size, pending_profiles)} profiles...\n")
                        
                        try:
                            # Call scrape_profile_activity command
                            call_command(
                                'scrape_profile_activity',
                                batch_size=batch_size,
                                min_comments=min_comments,
                                visible=visible,
                                scroll_limit=10
                            )
                            
                            # Check new posts discovered
                            new_pending = Post.objects.filter(scraped=False).count()
                            newly_discovered = new_pending - pending_count
                            
                            self.stdout.write(f"\nDiscovered {newly_discovered} new posts")
                            
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Error scraping activity: {str(e)}"))
                    else:
                        self.stdout.write(f"\nNo profiles with pending activity to scrape")
                
                depth += 1
                
                # Safety check
                if posts_scraped >= max_posts:
                    self.stdout.write(self.style.WARNING(f"\nReached max posts limit ({max_posts})"))
                    break
        
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\nScraping interrupted by user"))
            session.status = 'paused'
            session.ended_at = timezone.now()
            session.save()
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n\nFatal error: {str(e)}"))
            session.status = 'failed'
            session.ended_at = timezone.now()
            session.save()
            raise
        
        else:
            session.status = 'completed'
            session.ended_at = timezone.now()
            session.save()
        
        # Final summary
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("INFINITE SCRAPING SESSION COMPLETE"))
        self.stdout.write("="*70)
        self.stdout.write(f"Session ID: {session.id}")
        self.stdout.write(f"Status: {session.status}")
        self.stdout.write(f"Depth reached: {depth}")
        self.stdout.write(f"Posts scraped: {posts_scraped}")
        self.stdout.write(f"Total profiles: {Profile.objects.count()}")
        self.stdout.write(f"Total emails: {Contact.objects.count()}")
        self.stdout.write(f"Pending posts: {Post.objects.filter(scraped=False).count()}")
        self.stdout.write(f"Pending profiles: {Profile.objects.filter(activity_scraped=False).count()}")
        self.stdout.write("="*70)
