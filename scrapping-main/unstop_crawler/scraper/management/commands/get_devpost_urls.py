import time
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from browser_config import USER_DATA_DIR, PROFILE_NAME, BROWSER_BINARY


class Command(BaseCommand):
    help = """
    Get all unique hackathon URLs from Devpost.
    
    Fetches every hackathon URL from Devpost's discover page without duplicates.
    Supports filtering by status (open, ended, upcoming, etc).
    
    USAGE:
    
      # Get all hackathon URLs
      python manage.py get_devpost_urls
      
      # Get only open hackathons
      python manage.py get_devpost_urls --status open
      
      # Save to file
      python manage.py get_devpost_urls --output devpost_urls.txt
    
    EXAMPLES:
    
      # Get all URLs (headless mode)
      python manage.py get_devpost_urls --output devpost_urls.txt --headless
      
      # Get only open hackathons
      python manage.py get_devpost_urls --status open --headless
      
      # Get ended hackathons
      python manage.py get_devpost_urls --status ended --headless
      
      # Show statistics
      python manage.py get_devpost_urls --show-stats --headless
    
    OPTIONS:
      --status STATUS    Filter by status (open, ended, upcoming, etc)
      --output FILE      Save URLs to file
      --show-stats       Show statistics about URLs
      --headless         Run browser in headless mode (RECOMMENDED)
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            type=str,
            choices=['open', 'ended', 'upcoming', 'all'],
            default='all',
            help='Filter hackathons by status (default: all)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file to save URLs (optional)',
        )
        parser.add_argument(
            '--show-stats',
            action='store_true',
            help='Show statistics about the URLs',
        )
        parser.add_argument(
            '--headless',
            action='store_true',
            help='Run browser in headless mode',
        )

    def setup_driver(self, headless=False):
        """Setup Chrome driver with profile"""
        chrome_options = Options()
        chrome_options.binary_location = BROWSER_BINARY
        chrome_options.add_argument(f"user-data-dir={USER_DATA_DIR}")
        chrome_options.add_argument(f"profile-directory={PROFILE_NAME}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def get_all_urls(self, status='all', headless=False):
        """Fetch all hackathon URLs from Devpost using pagination"""
        all_urls = set()
        
        # Devpost loads more hackathons via AJAX as you scroll
        # We'll use a different approach: load the page and click "Load More" repeatedly
        
        # Build base URL based on status
        if status == 'all':
            base_url = "https://devpost.com/hackathons"
        else:
            base_url = f"https://devpost.com/hackathons?status={status}"
        
        self.stdout.write(f"Fetching URLs from: {base_url}")
        self.stdout.write("This will take 15-30 minutes to load all ~12,000 hackathons...")
        self.stdout.write("The page loads 25 hackathons at a time.")
        
        driver = self.setup_driver(headless)
        
        try:
            driver.get(base_url)
            time.sleep(5)
            
            load_more_clicks = 0
            consecutive_failures = 0
            max_clicks = 500  # ~12,500 hackathons max
            
            while load_more_clicks < max_clicks and consecutive_failures < 3:
                try:
                    # Extract current URLs before clicking
                    previous_count = len(all_urls)
                    soup = BeautifulSoup(driver.page_source, 'html.parser')
                    
                    # Find all hackathon links
                    # Devpost uses various patterns, let's be comprehensive
                    links = soup.find_all('a', href=True)
                    
                    for link in links:
                        href = link['href']
                        # Match *.devpost.com URLs but exclude specific paths
                        if '.devpost.com' in href:
                            # Exclude these patterns
                            if any(x in href for x in [
                                'devpost.com/hackathons',
                                'devpost.com/software',
                                'devpost.com/challenges',
                                'devpost.com/jobs',
                                'devpost.com/about',
                                'devpost.com/privacy',
                                'devpost.com/terms'
                            ]):
                                continue
                            
                            # Normalize URL
                            if href.startswith('//'):
                                href = 'https:' + href
                            elif href.startswith('/'):
                                continue
                            
                            # Clean URL (remove query params and fragments)
                            base_hack_url = href.split('?')[0].split('#')[0].rstrip('/')
                            
                            # Validate it's a hackathon subdomain
                            if base_hack_url.count('.devpost.com') == 1 and '://' in base_hack_url:
                                all_urls.add(base_hack_url)
                    
                    new_urls_found = len(all_urls) - previous_count
                    
                    # Progress update every 10 clicks
                    if load_more_clicks % 10 == 0 or new_urls_found > 0:
                        self.stdout.write(f"  Click #{load_more_clicks}: {len(all_urls)} total URLs (+{new_urls_found} new)")
                    
                    # Try to find and click "Load More" button
                    # Devpost uses various selectors for this
                    load_more_found = False
                    
                    # Try different selectors for the load more button
                    selectors = [
                        "//a[contains(@class, 'infinite-scroll-load-more')]",
                        "//a[contains(text(), 'Load more')]",
                        "//button[contains(text(), 'Load more')]",
                        "//a[@class='next_page']",
                        "//*[contains(@class, 'load-more')]",
                    ]
                    
                    for selector in selectors:
                        try:
                            load_more_button = WebDriverWait(driver, 3).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            
                            # Scroll button into view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", load_more_button)
                            time.sleep(0.5)
                            
                            # Click it
                            driver.execute_script("arguments[0].click();", load_more_button)
                            load_more_found = True
                            load_more_clicks += 1
                            
                            # Wait for new content to load
                            time.sleep(2)
                            
                            # Reset failure counter
                            consecutive_failures = 0
                            break
                            
                        except Exception:
                            continue
                    
                    if not load_more_found:
                        # If no load more button found, try scrolling
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)
                        
                        # Check if we got new content
                        if new_urls_found == 0:
                            consecutive_failures += 1
                            self.stdout.write(f"  No new URLs found (attempt {consecutive_failures}/3)")
                        else:
                            consecutive_failures = 0
                    
                except Exception as e:
                    self.stdout.write(f"  Error during scroll: {str(e)[:100]}")
                    consecutive_failures += 1
                    
                    if consecutive_failures >= 3:
                        self.stdout.write(f"  Stopping after {consecutive_failures} consecutive failures")
                        break
            
            self.stdout.write(f"\n✓ Completed after {load_more_clicks} load-more clicks")
            self.stdout.write(f"✓ Final count: {len(all_urls)} unique hackathon URLs")
                    
        finally:
            driver.quit()
        
        return sorted(all_urls)

    def handle(self, *args, **options):
        status = options['status']
        output_file = options.get('output')
        show_stats = options['show_stats']
        headless = options.get('headless', False)
        
        self.stdout.write(self.style.SUCCESS("Starting Devpost URL fetcher..."))
        if headless:
            self.stdout.write("Running in HEADLESS mode")
        
        # Get all URLs
        urls = self.get_all_urls(status, headless)
        
        # Show stats
        self.stdout.write(self.style.SUCCESS(f"\n✓ Found {len(urls)} unique hackathon URLs"))
        
        if show_stats:
            # Count by status (based on URL patterns)
            self.stdout.write("\nStatistics:")
            self.stdout.write(f"  Total URLs: {len(urls)}")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                for url in urls:
                    f.write(url + '\n')
            self.stdout.write(self.style.SUCCESS(f"\n✓ Saved to: {output_file}"))
        else:
            # Print to stdout
            self.stdout.write("\nURLs:")
            for url in urls:
                self.stdout.write(url)
