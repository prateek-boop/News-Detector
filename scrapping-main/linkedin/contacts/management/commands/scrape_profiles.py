from django.core.management.base import BaseCommand
from seleniumbase import SB
from contacts.models import Contact, Profile
import time
import re
import os

class Command(BaseCommand):
    help = 'Scrape LinkedIn profiles from comment authors on a LinkedIn post'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            required=True,
            help='LinkedIn post URL to scrape profiles from'
        )
        parser.add_argument(
            '--visible',
            action='store_true',
            help='Run browser in visible mode instead of headless (useful for debugging)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of profiles to scrape (useful for testing)'
        )

    def handle(self, *args, **options):
        url = options['url']
        headless = not options['visible']
        limit = options['limit']
        profile_dir = os.path.abspath("./profile")
        
        start_time = time.time()
        
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("LinkedIn Profile Scraper"))
        self.stdout.write(f"Target: {url}")
        self.stdout.write(f"Mode: {'HEADLESS' if headless else 'VISIBLE'}")
        if limit:
            self.stdout.write(f"Limit: {limit} profiles")
        self.stdout.write("="*70 + "\n")
        
        try:
            with SB(uc=True, headless=headless, user_data_dir=profile_dir) as sb:
                
                # STEP 1: Open post and load all comments
                self.stdout.write("Opening LinkedIn post...")
                sb.open(url)
                sb.sleep(5)
                
                if 'authwall' in sb.get_current_url() or 'login' in sb.get_current_url():
                    self.stdout.write(self.style.ERROR("  Error: Not logged in to LinkedIn"))
                    return
                
                # STEP 2: Load all comments
                self.stdout.write("Loading comments...")
                clicks = 0
                while True:
                    try:
                        sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        sb.sleep(0.5)
                        
                        button_found = False
                        selectors = [
                            "button.comments-comments-list__load-more-comments-button",
                            "button:contains('Load more comments')",
                            "button[aria-label*='Load more']"
                        ]
                        
                        for selector in selectors:
                            if sb.is_element_present(selector):
                                sb.click(selector)
                                button_found = True
                                clicks += 1
                                if clicks % 10 == 0:
                                    self.stdout.write(f"  Loaded {clicks} more comments...")
                                sb.sleep(0.8)
                                break
                        
                        if not button_found:
                            break
                            
                    except:
                        break
                
                self.stdout.write(f"Total comment loads: {clicks}\n")
                
                # STEP 3: Extract profile URLs from comments
                self.stdout.write("Extracting profile URLs...")
                profile_urls = sb.execute_script(r"""
                    const urls = new Set();
                    document.querySelectorAll('a[href*="/in/"]').forEach(link => {
                        const href = link.href;
                        if (href.includes('/in/') && !href.includes('/company/')) {
                            // Clean URL (remove query params and anchors)
                            const cleanUrl = href.split('?')[0].split('#')[0];
                            if (cleanUrl.match(/linkedin\.com\/in\/[^\/]+\/?$/)) {
                                urls.add(cleanUrl);
                            }
                        }
                    });
                    return Array.from(urls);
                """)
                
                if not profile_urls:
                    self.stdout.write(self.style.WARNING("  Warning: No profile URLs found"))
                    return
                
                self.stdout.write(f"Found {len(profile_urls)} unique profiles\n")
                
                # Apply limit if specified
                if limit:
                    profile_urls = profile_urls[:limit]
                    self.stdout.write(f"  Limiting to {limit} profiles\n")
                
                # STEP 4: Scrape each profile
                scraped_count = 0
                skipped_count = 0
                error_count = 0
                
                for idx, profile_url in enumerate(profile_urls, 1):
                    try:
                        # Check if already scraped
                        if Profile.objects.filter(linkedin_url=profile_url).exists():
                            self.stdout.write(f"  [{idx}/{len(profile_urls)}] Skipped (already exists): {profile_url}")
                            skipped_count += 1
                            continue
                        
                        self.stdout.write(f"  [{idx}/{len(profile_urls)}] Saving: {profile_url}")
                        
                        # Just save the URL, no detailed scraping
                        Profile.objects.create(
                            linkedin_url=profile_url,
                            contact=None
                        )
                        
                        scraped_count += 1
                        self.stdout.write(self.style.SUCCESS("    Saved URL"))
                        
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(self.style.ERROR(f"    Error: {str(e)}"))
                        continue
                
                # Final summary
                elapsed = time.time() - start_time
                self.stdout.write("\n" + "="*70)
                self.stdout.write(self.style.SUCCESS("SCRAPING SUMMARY"))
                self.stdout.write("="*70)
                self.stdout.write(f"Total profiles found:  {len(profile_urls)}")
                self.stdout.write(f"Successfully scraped:  {scraped_count}")
                self.stdout.write(f"Already existed:       {skipped_count}")
                self.stdout.write(f"Errors:                {error_count}")
                self.stdout.write(f"Time taken:            {elapsed:.1f}s")
                self.stdout.write("="*70)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nFatal error: {str(e)}"))
