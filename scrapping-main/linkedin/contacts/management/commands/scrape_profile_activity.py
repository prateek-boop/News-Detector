from django.core.management.base import BaseCommand
from django.utils import timezone
from seleniumbase import SB
from contacts.models import Profile, Post
import time
import re
import os

class Command(BaseCommand):
    help = 'Scrape posts from LinkedIn profiles recent activity to discover new posts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--profile-url',
            type=str,
            help='Specific profile URL to scrape (if not provided, scrapes pending profiles)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of profiles to process in batch (default: 50)'
        )
        parser.add_argument(
            '--min-comments',
            type=int,
            default=100,
            help='Minimum comment count to queue post (default: 100)'
        )
        parser.add_argument(
            '--visible',
            action='store_true',
            help='Run browser in visible mode'
        )
        parser.add_argument(
            '--scroll-limit',
            type=int,
            default=10,
            help='Maximum scrolls on activity page (default: 10)'
        )

    def handle(self, *args, **options):
        profile_url = options['profile_url']
        batch_size = options['batch_size']
        min_comments = options['min_comments']
        headless = not options['visible']
        scroll_limit = options['scroll_limit']
        profile_dir = os.path.abspath("./profile")
        
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("LinkedIn Profile Activity Scraper"))
        self.stdout.write(f"Mode: {'HEADLESS' if headless else 'VISIBLE'}")
        self.stdout.write(f"Min comments filter: {min_comments}")
        self.stdout.write(f"Scroll limit: {scroll_limit}")
        self.stdout.write("="*70)
        
        # Get profiles to scrape
        if profile_url:
            profiles = Profile.objects.filter(linkedin_url=profile_url)
            if not profiles.exists():
                self.stdout.write(self.style.ERROR(f"Profile not found: {profile_url}"))
                return
        else:
            profiles = Profile.objects.filter(activity_scraped=False).order_by('-scraped_at')[:batch_size]
        
        total_profiles = profiles.count()
        
        if total_profiles == 0:
            self.stdout.write(self.style.WARNING("No profiles to scrape"))
            return
        
        self.stdout.write(f"\nProcessing {total_profiles} profiles...\n")
        
        with SB(uc=True, headless=headless, user_data_dir=profile_dir) as sb:
            processed = 0
            total_posts_discovered = 0
            
            for profile in profiles:
                processed += 1
                
                try:
                    # Construct activity URL
                    base_url = profile.linkedin_url.rstrip('/')
                    activity_url = f"{base_url}/recent-activity/comments/"
                    
                    self.stdout.write(f"\n[{processed}/{total_profiles}] {activity_url}")
                    
                    # Visit activity page
                    sb.open(activity_url)
                    time.sleep(2)
                    
                    # Check if page loaded successfully
                    if "Page not found" in sb.get_page_source() or "This page doesn't exist" in sb.get_page_source():
                        self.stdout.write(self.style.WARNING("  Profile not accessible"))
                        profile.activity_scraped = True
                        profile.activity_scraped_at = timezone.now()
                        profile.save()
                        continue
                    
                    # Scroll to load more activity
                    posts_discovered = 0
                    for scroll in range(scroll_limit):
                        # Extract post URLs with JavaScript
                        post_urls = self._extract_post_urls(sb)
                        
                        # Queue new posts
                        for post_url in post_urls:
                            # Clean URL
                            clean_url = self._clean_post_url(post_url)
                            if not clean_url:
                                continue
                            
                            # Check if already exists
                            if Post.objects.filter(post_url=clean_url).exists():
                                continue
                            
                            # Create post entry
                            Post.objects.create(
                                post_url=clean_url,
                                comment_count=min_comments,  # Estimate, will be updated when scraped
                                discovered_from_profile=profile
                            )
                            posts_discovered += 1
                            total_posts_discovered += 1
                        
                        # Scroll down
                        sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1.5)
                    
                    # Mark profile as scraped
                    profile.activity_scraped = True
                    profile.activity_scraped_at = timezone.now()
                    profile.posts_discovered_count = posts_discovered
                    profile.save()
                    
                    self.stdout.write(self.style.SUCCESS(f"  Discovered {posts_discovered} new posts"))
                    
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING("\n\nInterrupted by user"))
                    profile.activity_scraped = True
                    profile.activity_scraped_at = timezone.now()
                    profile.save()
                    break
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error: {str(e)}"))
                    # Mark as scraped anyway to avoid retrying
                    profile.activity_scraped = True
                    profile.activity_scraped_at = timezone.now()
                    profile.save()
                    continue
        
        # Final summary
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("SCRAPING COMPLETE"))
        self.stdout.write("="*70)
        self.stdout.write(f"Profiles processed: {processed}")
        self.stdout.write(f"Posts discovered: {total_posts_discovered}")
        self.stdout.write(f"Posts in queue: {Post.objects.filter(scraped=False).count()}")
    
    def _extract_post_urls(self, sb):
        """Extract post URLs from current page using JavaScript"""
        js_code = """
        (function() {
            const postLinks = [];
            const links = document.querySelectorAll('a[href*="/posts/"], a[href*="/feed/update/"]');
            
            links.forEach(link => {
                const href = link.href;
                if (href && (href.includes('/posts/') || href.includes('/feed/update/'))) {
                    postLinks.push(href);
                }
            });
            
            return [...new Set(postLinks)];
        })();
        """
        
        try:
            urls = sb.execute_script(js_code)
            return urls if urls else []
        except Exception as e:
            return []
    
    def _clean_post_url(self, url):
        """Clean and normalize post URL"""
        if not url:
            return None
        
        # Remove query parameters and fragments
        url = url.split('?')[0].split('#')[0]
        
        # Must contain posts or feed/update
        if '/posts/' not in url and '/feed/update/' not in url:
            return None
        
        # Basic LinkedIn URL validation
        if not url.startswith('https://www.linkedin.com/'):
            return None
        
        return url
