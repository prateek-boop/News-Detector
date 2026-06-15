import time
import re
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from scraper.models import DevpostHackathon
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from browser_config import USER_DATA_DIR, PROFILE_NAME, BROWSER_BINARY


class Command(BaseCommand):
    help = """
    Scrape hackathons from Devpost (OPTIMIZED - extracts essential data only).
    
    This command extracts key hackathon data from Devpost:
    - ID, Name, Organizer
    - Participants count
    - Contact information
    - Sponsors
    
    USAGE MODES:
    
    1. Scrape from URL file (RECOMMENDED):
       python manage.py scrape_devpost --from-file devpost_all_urls.txt --headless
    
    2. Scrape specific URL:
       python manage.py scrape_devpost --url https://hackthetrack.devpost.com --headless
    
    EXAMPLES:
    
      # Scrape all URLs from file (headless mode)
      python manage.py scrape_devpost --from-file devpost_all_urls.txt --headless
      
      # Scrape specific hackathon and show extracted data
      python manage.py scrape_devpost --url https://hackthetrack.devpost.com --headless
      
      # Scrape first 10 from file
      python manage.py scrape_devpost --from-file devpost_all_urls.txt --limit 10 --headless
      
      # Update existing records (re-scrape to fix missing data)
      python manage.py scrape_devpost --url https://example.devpost.com --headless --update-database
    
    OPTIONS:
      --from-file FILE    Read URLs from file (one per line)
      --url URL           Scrape specific hackathon URL
      --limit N           Limit number of hackathons to scrape
      --skip-existing     Skip already scraped hackathons (default: True)
      --headless          Run browser in headless mode (RECOMMENDED)
      --update-database   Update existing records (default: only create new)
    
    RECOMMENDED WORKFLOW:
      1. Get all URLs: python manage.py get_devpost_urls_api
      2. Scrape data:   python manage.py scrape_devpost --from-file devpost_all_urls.txt --headless
      3. Export:        python manage.py export_devpost --format json
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--from-file',
            type=str,
            help='Read URLs from file (one URL per line)',
        )
        parser.add_argument(
            '--url',
            type=str,
            help='Scrape specific hackathon URL',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of hackathons to scrape',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            default=True,
            help='Skip hackathons already in database (default: True)',
        )
        parser.add_argument(
            '--headless',
            action='store_true',
            help='Run browser in headless mode (RECOMMENDED)',
        )
        parser.add_argument(
            '--update-database',
            action='store_true',
            help='Update existing records in database (default: only create new)',
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
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver

    def scrape_hackathon_page(self, url, headless=False):
        """Scrape a single hackathon page - optimized for essential data"""
        chrome_options = Options()
        chrome_options.binary_location = BROWSER_BINARY
        
        if headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
        else:
            chrome_options.add_argument(f"user-data-dir={USER_DATA_DIR}")
            chrome_options.add_argument(f"profile-directory={PROFILE_NAME}")
        
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            self.stdout.write(f"  Fetching: {url}")
            driver.get(url)
            time.sleep(5)
            
            # Scroll to load all content including sidebar
            for _ in range(3):
                driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Extract name
            name = ""
            name_elem = soup.find('h1', id='challenge-title')
            if not name_elem:
                name_elem = soup.find('h1', class_='challenge-title')
            if not name_elem:
                name_elem = soup.find('h1')
            if name_elem:
                name = name_elem.get_text(strip=True)
            
            # Fallback: extract from URL
            if not name:
                name = url.replace('https://', '').replace('.devpost.com', '').replace('-', ' ').title()
            
            # Extract participants count - PRIORITY: sidebar stats
            participants_count = ""
            
            # Method 1: Check sidebar stats area (most reliable)
            try:
                stats_elem = driver.find_element(By.ID, 'challenge-stats')
                stats_html = stats_elem.get_attribute('outerHTML')
                stats_soup = BeautifulSoup(stats_html, 'html.parser')
                text_content = stats_soup.get_text()
                
                # Match patterns like "1,234 participants"
                participant_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*participants?', text_content, re.IGNORECASE)
                if participant_match:
                    participants_count = participant_match.group(1).replace(',', '')
            except:
                pass
            
            # Method 2: Search entire page if not found
            if not participants_count:
                page_text = soup.get_text()
                participant_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*participants?', page_text, re.IGNORECASE)
                if participant_match:
                    participants_count = participant_match.group(1).replace(',', '')
            
            # Get sidebar element for later use (initialize here to avoid scope issues)
            sidebar = soup.find(id='challenge-sponsors-side')
            
            # Extract organizer - IMPROVED EXTRACTION
            organizer = ""
            
            # Method 1: Extract from page title (most reliable)
            title_elem = soup.find('title')
            if title_elem:
                title_text = title_elem.get_text()
                # Try "hackathon name | Devpost" pattern - extract before |
                if ' | Devpost' in title_text:
                    hackathon_part = title_text.split(' | Devpost')[0].strip()
                    # Now try to extract organizer from hackathon name
                    # Pattern: "Name presented by Org" or "Name by Org"
                    presented_match = re.search(r'(?:presented|hosted|powered)\s+by\s+(.+)', hackathon_part, re.IGNORECASE)
                    if presented_match:
                        organizer = presented_match.group(1).strip()
            
            # Method 2: Look in main content for "hosted by", "organized by", etc.
            if not organizer:
                page_text = soup.get_text()
                org_patterns = [
                    r'(?:hosted|organized|presented|powered)\s+by\s+([A-Z][A-Za-z0-9\s&.,]+?)(?:\n|$|!|\?)',
                    r'Organizer[:\s]+([A-Z][A-Za-z0-9\s&.,]+?)(?:\n|$)',
                    r'brought to you by\s+([A-Z][A-Za-z0-9\s&.,]+?)(?:\n|$|!|\?)',
                ]
                for pattern in org_patterns:
                    match = re.search(pattern, page_text, re.IGNORECASE)
                    if match:
                        org_name = match.group(1).strip()
                        # Clean up common trailing words
                        org_name = re.sub(r'\s+(in|at|for|and|with|the)\s*$', '', org_name, flags=re.IGNORECASE)
                        if org_name and org_name.lower() not in ['devpost', 'the', 'a', 'an'] and len(org_name) > 2:
                            organizer = org_name
                            break
            
            # Method 3: Extract organizer from hackathon name (prefer over sponsors)
            if not organizer and name:
                # Pattern: "Name YEAR" -> extract "Name"
                # Remove years, common hackathon words
                org_from_name = re.sub(r'\b(20\d{2}|hackathon|ideathon|datathon|competition)\b', '', name, flags=re.IGNORECASE).strip()
                if org_from_name and len(org_from_name) > 3:
                    organizer = org_from_name
            
            # Method 4: Look for sponsor names as last resort (skip if too short or generic)
            if not organizer and sidebar:
                # Look for first sponsor img with alt text (usually main organizer)
                sponsor_imgs = sidebar.find_all('img', alt=True)
                for img in sponsor_imgs:
                    alt_text = img.get('alt', '').strip()
                    # Skip generic/short terms
                    if (alt_text and 
                        'logo' not in alt_text.lower() and 
                        'devpost' not in alt_text.lower() and
                        not alt_text.startswith('.') and  # Skip domain extensions like .xyz
                        not alt_text.endswith('.xyz') and  # Skip .xyz domains
                        not alt_text.endswith('.io') and  # Skip .io domains
                        not alt_text.endswith('.com') and  # Skip .com domains
                        len(alt_text) > 3):
                        organizer = alt_text
                        break
            
            # Extract contact details - IMPROVED EXTRACTION
            organizer_contact = ""
            contact_info = []
            seen_emails = set()
            
            # Method 1: Look for contact in details section
            details_section = soup.find('div', id='challenge-details')
            if details_section:
                # Find all email links in details
                emails = details_section.find_all('a', href=re.compile(r'^mailto:'))
                for email in emails:
                    email_addr = email.get('href', '').replace('mailto:', '').strip().lower()
                    if email_addr and '@' in email_addr and email_addr not in seen_emails:
                        contact_info.append(f"Email: {email_addr}")
                        seen_emails.add(email_addr)
            
            # Method 2: Check sidebar for contact
            if sidebar:
                emails = sidebar.find_all('a', href=re.compile(r'^mailto:'))
                for email in emails:
                    email_addr = email.get('href', '').replace('mailto:', '').strip().lower()
                    if email_addr and '@' in email_addr and email_addr not in seen_emails:
                        contact_info.append(f"Email: {email_addr}")
                        seen_emails.add(email_addr)
            
            # Method 3: Search entire page for mailto links
            if not contact_info:
                emails = soup.find_all('a', href=re.compile(r'^mailto:'))
                for email in emails[:5]:  # Limit to first 5
                    email_addr = email.get('href', '').replace('mailto:', '').strip().lower()
                    if email_addr and '@' in email_addr and email_addr not in seen_emails:
                        contact_info.append(f"Email: {email_addr}")
                        seen_emails.add(email_addr)
            
            organizer_contact = '\n'.join(contact_info) if contact_info else ""
            
            # Extract sponsors - EXTRACT URLs (hrefs)
            sponsors = ""
            sponsor_links = []
            seen_sponsors = set()
            
            if sidebar:
                try:
                    # Extract all links (hrefs) from sponsor section
                    sponsor_anchors = sidebar.find_all('a', href=True)
                    for anchor in sponsor_anchors:
                        href = anchor.get('href', '').strip()
                        # Filter valid URLs (skip mailto, javascript, etc.)
                        if (href and 
                            href.startswith('http') and 
                            href not in seen_sponsors and
                            'devpost.com' not in href):  # Exclude Devpost internal links
                            sponsor_links.append(href)
                            seen_sponsors.add(href)
                    
                    sponsors = '\n'.join(sponsor_links) if sponsor_links else ""
                except Exception as e:
                    self.stdout.write(f"    Warning: Error extracting sponsors: {str(e)}")
            
            # Extract about content
            about_content = ""
            try:
                # Look for the main description/about section
                about_section = soup.find('div', id='challenge-details')
                if not about_section:
                    about_section = soup.find('div', class_=re.compile(r'challenge.*detail', re.IGNORECASE))
                if not about_section:
                    # Try to find the main content area
                    about_section = soup.find('div', class_='content')
                
                if about_section:
                    # Get text but clean it up
                    about_text = about_section.get_text(separator='\n', strip=True)
                    # Remove excessive whitespace
                    about_text = re.sub(r'\n\s*\n', '\n\n', about_text)
                    # Limit length
                    about_content = about_text[:5000] if about_text else ""
            except:
                pass
            
            return {
                'name': name,
                'organizer': organizer,
                'participants_count': participants_count,
                'organizer_contact': organizer_contact,
                'sponsors': sponsors,
                'about_content': about_content
            }
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Error scraping {url}: {str(e)}"))
            return None
        finally:
            driver.quit()

    def scrape_from_file(self, filename, skip_existing=True, limit=None, headless=False, update_database=False):
        """Scrape hackathons from a file containing URLs"""
        try:
            with open(filename, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and '.devpost.com' in line]
            
            self.stdout.write(f"Loaded {len(urls)} Devpost URLs from {filename}")
            
            if skip_existing:
                existing_urls = set(DevpostHackathon.objects.values_list('url', flat=True))
                new_urls = [url for url in urls if url not in existing_urls]
                self.stdout.write(f"After filtering: {len(new_urls)} new hackathons to scrape")
                urls = new_urls
            
            if limit:
                urls = urls[:limit]
                self.stdout.write(f"Limited to: {len(urls)} hackathons")
            
            # Scrape each URL
            updated_count = 0
            created_count = 0
            error_count = 0
            
            for idx, url in enumerate(urls, 1):
                self.stdout.write(f"\n[{idx}/{len(urls)}] Processing: {url}")
                
                try:
                    data = self.scrape_hackathon_page(url, headless)
                    
                    if not data or not data.get('name'):
                        self.stdout.write(self.style.ERROR(f"  ✗ Failed to extract data"))
                        error_count += 1
                        continue
                    
                    # Save to database (only essential fields)
                    hackathon, created = DevpostHackathon.objects.update_or_create(
                        url=url,
                        defaults={
                            "name": data['name'],
                            "organizer": data['organizer'],
                            "participants_count": data['participants_count'],
                            "organizer_contact": data['organizer_contact'],
                            "sponsors": data['sponsors'],
                            "about_content": data.get('about_content', ''),
                        },
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Created: {data['name']}"))
                        if data['participants_count']:
                            self.stdout.write(f"    Participants: {data['participants_count']}")
                        created_count += 1
                    else:
                        self.stdout.write(self.style.WARNING(f"  ↻ Updated: {data['name']}"))
                        if data['participants_count']:
                            self.stdout.write(f"    Participants: {data['participants_count']}")
                        updated_count += 1
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))
                    error_count += 1
            
            # Summary
            self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
            self.stdout.write(self.style.SUCCESS(f"Scraping completed!"))
            self.stdout.write(f"  Created: {created_count}")
            self.stdout.write(f"  Updated: {updated_count}")
            self.stdout.write(f"  Errors: {error_count}")
            self.stdout.write(f"  Total processed: {len(urls)}")
                    
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {filename}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def handle(self, *args, **options):
        from_file = options.get('from_file')
        url = options.get('url')
        limit = options.get('limit')
        skip_existing = options['skip_existing']
        headless = options.get('headless', False)
        update_database = options.get('update_database', False)
        
        self.stdout.write(self.style.SUCCESS("Starting Devpost hackathon scraper..."))
        if headless:
            self.stdout.write("Running in HEADLESS mode")
        if update_database:
            self.stdout.write("Update mode: Will update existing records")
        
        if from_file:
            # Scrape from file
            self.scrape_from_file(from_file, skip_existing, limit, headless, update_database)
        elif url:
            # Scrape single URL
            self.stdout.write(f"Scraping: {url}")
            data = self.scrape_hackathon_page(url, headless)
            
            if not data or not data.get('name'):
                self.stdout.write(self.style.ERROR("✗ Failed to extract data"))
                return
            
            hackathon, created = DevpostHackathon.objects.update_or_create(
                url=url,
                defaults={
                    "name": data['name'],
                    "organizer": data['organizer'],
                    "participants_count": data['participants_count'],
                    "organizer_contact": data['organizer_contact'],
                    "sponsors": data['sponsors'],
                    "about_content": data.get('about_content', ''),
                },
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"✓ Created: {data['name']}"))
            else:
                self.stdout.write(self.style.WARNING(f"↻ Updated: {data['name']}"))
            
            # Display extracted data
            self.stdout.write(f"\n{'-'*60}")
            self.stdout.write(f"Name: {data['name']}")
            self.stdout.write(f"Organizer: {data['organizer']}")
            self.stdout.write(f"Participants: {data['participants_count']}")
            self.stdout.write(f"Contact: {data['organizer_contact']}")
            self.stdout.write(f"Sponsors: {data['sponsors']}")
            self.stdout.write(f"About (length): {len(data.get('about_content', ''))} chars")
        else:
            self.stdout.write(self.style.ERROR("Please specify --from-file or --url"))
