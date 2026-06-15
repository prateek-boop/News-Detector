import re
import time
from django.core.management.base import BaseCommand
from scraper.models import DevfolioHackathon
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from browser_config import USER_DATA_DIR, PROFILE_NAME, BROWSER_BINARY


class Command(BaseCommand):
    help = """
    Extract social media links (Telegram, Discord, LinkedIn, Twitter) from Devfolio hackathons.
    
    This command scrapes social media links from hackathon pages and updates the database.
    
    USAGE:
    
      # Extract from all hackathons
      python manage.py extract_devfolio_social --all
      
      # Extract from hackathons missing social links
      python manage.py extract_devfolio_social --missing-only
      
      # Extract from specific URL
      python manage.py extract_devfolio_social --url <devfolio-url>
      
      # Extract from specific ID
      python manage.py extract_devfolio_social --id 5
    
    EXAMPLES:
    
      # Update all hackathons
      python manage.py extract_devfolio_social --all
      
      # Update only those missing social links
      python manage.py extract_devfolio_social --missing-only
      
      # Limit to first 20
      python manage.py extract_devfolio_social --all --limit 20
    
    OPTIONS:
      --all            Extract from all hackathons
      --missing-only   Only extract from hackathons without social links
      --url URL        Extract from specific URL
      --id ID          Extract from specific database ID
      --limit N        Limit to N hackathons
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Extract from all hackathons',
        )
        parser.add_argument(
            '--missing-only',
            action='store_true',
            help='Only extract from hackathons missing social links',
        )
        parser.add_argument(
            '--url',
            type=str,
            help='Extract from specific hackathon URL',
        )
        parser.add_argument(
            '--id',
            type=int,
            help='Extract from specific hackathon ID',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of hackathons to process',
        )

    def extract_social_links(self, driver, url):
        """Extract all social media links from a Devfolio page"""
        social_links = {
            'telegram': None,
            'discord': None,
            'linkedin': None,
            'twitter': None,
        }
        
        try:
            driver.get(url)
            time.sleep(3)  # Wait for page load
            
            # Get all links on the page
            links = driver.find_elements(By.TAG_NAME, 'a')
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue
                    
                    # Check for Telegram
                    if 't.me' in href or 'telegram.me' in href or 'telegram.org' in href:
                        if not social_links['telegram']:
                            social_links['telegram'] = href
                    
                    # Check for Discord
                    elif 'discord.gg' in href or 'discord.com/invite' in href:
                        if not social_links['discord']:
                            social_links['discord'] = href
                    
                    # Check for LinkedIn
                    elif 'linkedin.com' in href:
                        if not social_links['linkedin']:
                            social_links['linkedin'] = href
                    
                    # Check for Twitter/X
                    elif 'twitter.com' in href or 'x.com' in href:
                        if not social_links['twitter']:
                            social_links['twitter'] = href
                            
                except Exception as e:
                    continue
            
            # Also check in about/description text for links
            try:
                page_text = driver.find_element(By.TAG_NAME, 'body').text
                
                # Extract Telegram links from text
                if not social_links['telegram']:
                    telegram_match = re.search(r'https?://(?:t\.me|telegram\.me)/[\w/]+', page_text)
                    if telegram_match:
                        social_links['telegram'] = telegram_match.group(0)
                
                # Extract Discord links from text
                if not social_links['discord']:
                    discord_match = re.search(r'https?://discord\.gg/[\w]+', page_text)
                    if discord_match:
                        social_links['discord'] = discord_match.group(0)
                        
            except Exception as e:
                pass
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error extracting links: {str(e)}"))
        
        return social_links

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Devfolio social media link extractor..."))
        
        # Determine which hackathons to process
        if options['url']:
            try:
                hackathons = [DevfolioHackathon.objects.get(url=options['url'])]
            except DevfolioHackathon.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Hackathon not found: {options['url']}"))
                return
        elif options['id']:
            try:
                hackathons = [DevfolioHackathon.objects.get(id=options['id'])]
            except DevfolioHackathon.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Hackathon not found with ID: {options['id']}"))
                return
        elif options['missing_only']:
            hackathons = DevfolioHackathon.objects.filter(
                telegram_link__isnull=True,
                discord_link__isnull=True,
                linkedin_link__isnull=True,
                twitter_link__isnull=True,
            )
        elif options['all']:
            hackathons = DevfolioHackathon.objects.all()
        else:
            self.stdout.write(self.style.ERROR("Please specify --all, --missing-only, --url, or --id"))
            return
        
        if options['limit']:
            hackathons = hackathons[:options['limit']]
        
        total = hackathons.count() if hasattr(hackathons, 'count') else len(hackathons)
        self.stdout.write(f"Processing {total} hackathons...")
        
        # Setup Selenium
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument(f"user-data-dir={USER_DATA_DIR}")
        chrome_options.add_argument(f"profile-directory={PROFILE_NAME}")
        chrome_options.binary_location = BROWSER_BINARY
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        updated = 0
        skipped = 0
        
        try:
            for idx, hackathon in enumerate(hackathons, 1):
                self.stdout.write(f"\n[{idx}/{total}] Processing: {hackathon.name}")
                self.stdout.write(f"  URL: {hackathon.url}")
                
                try:
                    # Extract social links
                    social_links = self.extract_social_links(driver, hackathon.url)
                    
                    # Update database
                    updated_fields = []
                    if social_links['telegram']:
                        hackathon.telegram_link = social_links['telegram']
                        updated_fields.append('Telegram')
                    if social_links['discord']:
                        hackathon.discord_link = social_links['discord']
                        updated_fields.append('Discord')
                    if social_links['linkedin']:
                        hackathon.linkedin_link = social_links['linkedin']
                        updated_fields.append('LinkedIn')
                    if social_links['twitter']:
                        hackathon.twitter_link = social_links['twitter']
                        updated_fields.append('Twitter')
                    
                    if updated_fields:
                        hackathon.save()
                        updated += 1
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Updated: {', '.join(updated_fields)}"))
                    else:
                        skipped += 1
                        self.stdout.write(self.style.WARNING(f"  ○ No social links found"))
                    
                except Exception as e:
                    skipped += 1
                    self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))
                
                time.sleep(1)  # Be respectful to the server
        
        finally:
            driver.quit()
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
        self.stdout.write(self.style.SUCCESS(f"Extraction completed!"))
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated}"))
        self.stdout.write(self.style.WARNING(f"  Skipped: {skipped}"))
        self.stdout.write(self.style.SUCCESS(f"  Total: {total}"))
