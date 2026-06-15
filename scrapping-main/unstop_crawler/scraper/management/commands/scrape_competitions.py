import time
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from scraper.models import Competition
import json
import re
from browser_config import USER_DATA_DIR, PROFILE_NAME, BROWSER_BINARY, USER_AGENT
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading


class Command(BaseCommand):
    help = """
    Scrape all competitions from Unstop.
    
    Similar to hackathons but targets the competitions category.
    
    This command extracts comprehensive competition data including:
    - Name, organizer, registration/impression counts
    - About content, contact information
    - Important dates, official website, prizes
    
    USAGE MODES:
    
    1. API Mode (Default - Faster, more reliable):
       python manage.py scrape_competitions --limit 50
    
    2. From URL File:
       python manage.py scrape_competitions --from-file competition_urls.txt
    
    EXAMPLES:
    
      # Scrape first 10 competitions
      python manage.py scrape_competitions --limit 10
      
      # Rescrape all existing competitions
      python manage.py scrape_competitions --force-rescrape
      
      # Start from page 5
      python manage.py scrape_competitions --start-page 5
      
      # Scrape from URL file (only /competitions/ URLs)
      python manage.py scrape_competitions --from-file urls.txt --limit 100
      
      # Skip first 50 competitions
      python manage.py scrape_competitions --skip-competitions 50
    
    OPTIONS:
      --limit N                Scrape only N competitions
      --skip-existing          Skip already scraped (default: True)
      --force-rescrape         Rescrape even if already in database
      --start-page N           Start from page N of API results
      --skip-pages N           Skip first N pages
      --skip-competitions N    Skip first N competitions
      --from-file FILE         Read URLs from file (one per line)
      --use-selenium           Use Selenium browser (not recommended)
    
    NOTE: Competitions use logged-in browser profile for contact extraction.
          Wait times: ~19 seconds per competition for full data.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--use-selenium",
            action="store_true",
            help="Use Selenium (requires Chrome/Chromium installed)",
        )
        parser.add_argument(
            "--headless",
            action="store_true",
            help="Run browser in headless mode (only with --use-selenium)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of competitions to scrape",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            default=True,
            help="Skip competitions already in database (default: True)",
        )
        parser.add_argument(
            "--force-rescrape",
            action="store_true",
            help="Rescrape all competitions even if already in database",
        )
        parser.add_argument(
            "--skip-pages",
            type=int,
            default=0,
            help="Skip first N pages before starting to scrape (default: 0)",
        )
        parser.add_argument(
            "--skip-competitions",
            type=int,
            default=0,
            help="Skip first N competitions before starting to scrape (default: 0)",
        )
        parser.add_argument(
            "--start-page",
            type=int,
            default=1,
            help="Start scraping from specific page number (default: 1)",
        )
        parser.add_argument(
            "--from-file",
            type=str,
            help="Read URLs from file (one URL per line). Only scrapes /competitions/ URLs",
        )
        parser.add_argument(
            "--concurrent",
            type=int,
            default=1,
            help="Number of concurrent workers for parallel scraping (default: 1, recommended: 3-5)",
        )

    def handle(self, *args, **options):
        use_selenium = options["use_selenium"]
        headless = options["headless"]
        limit = options["limit"]
        skip_existing = options["skip_existing"] and not options["force_rescrape"]
        skip_pages = options["skip_pages"]
        skip_competitions = options["skip_competitions"]
        start_page = options["start_page"]
        from_file = options.get("from_file")
        concurrent_workers = options.get("concurrent", 1)

        self.stdout.write(self.style.SUCCESS("Starting Unstop competition scraper..."))
        
        # Show concurrency info
        if concurrent_workers > 1:
            self.stdout.write(self.style.SUCCESS(f"⚡ Concurrent mode: {concurrent_workers} workers"))
        
        # Handle file-based scraping
        if from_file:
            self.scrape_from_file(from_file, skip_existing, limit, concurrent_workers)
            return
        
        if skip_existing:
            self.stdout.write(self.style.SUCCESS("Skip existing: Enabled (will only scrape new competitions)"))
        else:
            self.stdout.write(self.style.WARNING("Skip existing: Disabled (will rescrape all competitions)"))
        
        if start_page > 1:
            self.stdout.write(self.style.WARNING(f"Starting from page: {start_page}"))
        
        if skip_pages > 0:
            self.stdout.write(self.style.WARNING(f"Skipping first {skip_pages} pages"))
        
        if skip_competitions > 0:
            self.stdout.write(self.style.WARNING(f"Skipping first {skip_competitions} competitions"))

        if use_selenium:
            self.stdout.write(
                self.style.WARNING("Using Selenium mode (requires Chrome/Chromium)")
            )
            self.scrape_with_selenium(headless, limit)
        else:
            self.stdout.write(
                self.style.SUCCESS("Using requests mode (faster, no browser needed)")
            )
            self.scrape_with_requests(limit, skip_existing, skip_pages, skip_competitions, start_page)

        self.stdout.write(self.style.SUCCESS("Scraping completed!"))

    def scrape_with_requests(self, limit=None, skip_existing=True, skip_pages=0, skip_competitions=0, start_page=1):
        """Scrape using requests and Unstop API (no browser needed)"""

        # Get competition data from API
        competitions_data = self.get_competitions_from_api(limit, skip_existing, skip_pages, skip_competitions, start_page)
        self.stdout.write(
            self.style.SUCCESS(f"Found {len(competitions_data)} new competitions to scrape")
        )

        # Save each competition
        for idx, hack_data in enumerate(competitions_data, 1):
            self.stdout.write(
                f"Processing {idx}/{len(competitions_data)}: {hack_data.get('title', 'Unknown')}"
            )
            try:
                self.save_competition_from_api(hack_data)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error saving competition: {str(e)}"))

    def get_competitions_from_api(self, limit=None, skip_existing=True, skip_pages=0, skip_competitions=0, start_page=1):
        """Get competition data from Unstop's API"""
        all_competitions = []
        seen_urls = set()
        duplicates_in_row = 0
        max_duplicates_before_stop = 20  # Stop if we see 20 duplicates in a row
        competitions_skipped = 0

        try:
            self.stdout.write("Fetching competitions from Unstop API...")

            # Start from specified page or skip pages
            page = max(start_page, skip_pages + 1)
            max_pages = 100  # Unstop has many pages

            while page <= max_pages:
                # Use Unstop's public API endpoint
                api_url = f"https://unstop.com/api/public/opportunity/search-result?opportunity=competitions&page={page}"

                self.stdout.write(f"Fetching page {page}...")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Referer": "https://unstop.com/",
                }
                response = requests.get(api_url, headers=headers, timeout=30)
                response.raise_for_status()

                data = response.json()

                # Check if we have data
                if "data" not in data or "data" not in data["data"]:
                    break

                competitions = data["data"]["data"]

                if not competitions:
                    break

                # Track duplicates on this page
                page_duplicates = 0
                page_new = 0

                # Add competitions to our list (skip duplicates)
                for competition in competitions:
                    public_url = competition.get("public_url", "")
                    if not public_url.startswith("http"):
                        url = f"https://unstop.com/{public_url}"
                    else:
                        url = public_url
                    
                    # Check if we've already seen this URL in this session
                    if url in seen_urls:
                        page_duplicates += 1
                        duplicates_in_row += 1
                        continue
                    
                    # Check if already in database (only if skip_existing is True)
                    if skip_existing and Competition.objects.filter(url=url).exists():
                        page_duplicates += 1
                        duplicates_in_row += 1
                        continue
                    
                    # Skip competitions if skip_competitions is set
                    if skip_competitions > 0 and competitions_skipped < skip_competitions:
                        competitions_skipped += 1
                        page_duplicates += 1  # Count as skipped for display
                        continue
                    
                    # New competition
                    seen_urls.add(url)
                    all_competitions.append(competition)
                    page_new += 1
                    duplicates_in_row = 0  # Reset counter

                    if limit and len(all_competitions) >= limit:
                        return all_competitions[:limit]

                self.stdout.write(f"Page {page}: {page_new} new, {page_duplicates} duplicates/already scraped")

                # Stop if we're only seeing duplicates (only when skip_existing is True)
                if skip_existing and duplicates_in_row >= max_duplicates_before_stop:
                    self.stdout.write(self.style.WARNING(
                        f"Stopping: Found {duplicates_in_row} consecutive duplicates. All new competitions likely scraped."
                    ))
                    break

                # Check pagination
                if "last_page" in data["data"]:
                    last_page = data["data"]["last_page"]
                    if page >= last_page:
                        break

                page += 1
                time.sleep(0.5)  # Be respectful

            self.stdout.write(
                self.style.SUCCESS(f"Fetched {len(all_competitions)} new competitions from API")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching from API: {str(e)}"))
            import traceback

            self.stdout.write(traceback.format_exc())

        return all_competitions

    def save_competition_from_api(self, data):
        """Save competition data from API response"""
        # Extract data from API response
        public_url = data.get("public_url", "")
        if not public_url.startswith("http"):
            url = f"https://unstop.com/{public_url}"
        else:
            url = public_url

        # Extract basic info
        name = data.get("title", "Unknown")

        # Get organizer info
        organizer = ""
        if "organisation" in data and data["organisation"]:
            organizer = data["organisation"].get("name", "")

        # Get registration and impression counts from API
        registration_count = str(data.get("registerCount", "")) if data.get("registerCount") else ""
        impression_count = str(data.get("viewsCount", "")) if data.get("viewsCount") else ""
        
        # Legacy registered_count for backward compatibility
        registered_count = registration_count if registration_count else ""

        # Extract dates from API
        important_dates = self.extract_dates_from_api(data)
        
        # Extract prizes from API
        prizes = self.extract_prizes_from_api(data)

        # Still need to scrape individual page for detailed content and contact
        about_content, organizer_contact, official_website = (
            self.scrape_competition_page(url)
        )

        # Save to database
        competition, created = Competition.objects.update_or_create(
            url=url,
            defaults={
                "name": name,
                "organizer": organizer,
                "registered_count": registered_count,
                "registration_count": registration_count,
                "impression_count": impression_count,
                "about_content": about_content,
                "organizer_contact": organizer_contact,
                "important_dates": important_dates,
                "official_website": official_website,
                "prizes": prizes,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Created: {name}"))
        else:
            self.stdout.write(self.style.WARNING(f"↻ Updated: {name}"))
            
        if registration_count:
            self.stdout.write(f"  Registrations: {registration_count}")
        if impression_count:
            self.stdout.write(f"  Impressions: {impression_count}")
    
    def extract_dates_from_api(self, data):
        """Extract important dates from API data"""
        dates = []
        
        # Start and end dates
        if data.get("start_date"):
            dates.append(f"Start: {data['start_date']}")
        if data.get("end_date"):
            dates.append(f"End: {data['end_date']}")
        
        # Registration requirements
        if "regnRequirements" in data and data["regnRequirements"]:
            regn = data["regnRequirements"]
            if regn.get("start_regn_dt"):
                dates.append(f"Registration Start: {regn['start_regn_dt']}")
            if regn.get("end_regn_dt"):
                dates.append(f"Registration Deadline: {regn['end_regn_dt']}")
            if regn.get("remain_days"):
                dates.append(f"Status: {regn['remain_days']}")
        
        return "\n".join(dates) if dates else ""
    
    def extract_prizes_from_api(self, data):
        """Extract prize information from API data"""
        if "prizes" not in data or not data["prizes"]:
            return ""
        
        prizes_list = []
        for prize in data["prizes"]:
            rank = prize.get("rank", "")
            cash = prize.get("cash")
            others = prize.get("others")
            
            prize_text = rank
            if cash:
                prize_text += f": ₹{cash}"
            if others:
                prize_text += f" + {others}"
            
            if prize_text:
                prizes_list.append(prize_text)
        
        return "\n".join(prizes_list) if prizes_list else ""

    def scrape_competition_page(self, url):
        """Scrape individual competition page for detailed info using Selenium"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Import from browser_config
        from browser_config import USER_DATA_DIR, PROFILE_NAME, BROWSER_BINARY, USER_AGENT

        chrome_options = Options()
        
        # Use existing Chromium profile from config
        chrome_options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
        chrome_options.add_argument(f"--profile-directory={PROFILE_NAME}")
        
        # Use headless mode - works with logged-in profile
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(f"user-agent={USER_AGENT}")
        chrome_options.binary_location = BROWSER_BINARY

        driver = None
        try:
            # Use webdriver-manager to handle ChromeDriver automatically
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Navigate to the competition page
            driver.get(url)

            # Wait for initial page load (longer for logged-in content)
            time.sleep(8)
            
            # Scroll down to load lazy-loaded content (especially contact info)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(3)
            
            # Additional wait for AJAX/dynamic content to load
            time.sleep(5)

            # Get page source after JavaScript execution and scrolling
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Extract data
            about_content = self.extract_about_content(soup)
            
            # Try to extract contact from "Contact the organisers" section
            organizer_contact = ""
            
            # Method 1: Look for "Contact the organisers" section
            contact_header = soup.find(string=lambda t: t and "Contact the organisers" in t)
            if contact_header:
                # Find the container div after the header
                parent = contact_header.find_parent()
                if parent:
                    container = parent.find_next_sibling()
                    if not container:
                        container = parent.find_parent()
                    
                    if container:
                        # Extract all contact links - they can have different color classes
                        contact_links = container.find_all('a', class_=lambda c: c and ('text-hover' in ' '.join(c) if isinstance(c, list) else 'text-hover' in c))
                        contacts = []
                        for link in contact_links:
                            text = link.get_text(strip=True)
                            # Filter out Unstop support and empty
                            if text and '+91-9311777388' not in text and 'unstop' not in text.lower():
                                contacts.append(text)
                        
                        if contacts:
                            organizer_contact = " | ".join(contacts)
            
            # Method 2: If not found, look for general contact patterns
            if not organizer_contact:
                organizer_contact = self.extract_organizer_contact(soup)
            
            official_website = self.extract_official_website(soup)

            return about_content, organizer_contact, official_website

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Could not scrape page details: {str(e)}")
            )
            return "", "", ""
        finally:
            if driver:
                driver.quit()

    def extract_registered_count(self, soup):
        """Extract number of registered participants and impressions"""
        registration_count = ""
        impression_count = ""
        
        # Get full page text for pattern matching
        full_text = soup.get_text()
        
        # METHOD 1: Look for "Registered" label followed by number (for /competitions/ pages)
        # Pattern: "Registered\n801" or "Registered 801"
        reg_match = re.search(
            r"Registered\s*\n?\s*([\d,]+)", full_text, re.IGNORECASE
        )
        if reg_match:
            registration_count = reg_match.group(1).replace(",", "")
        
        # Look for "Impressions" followed by a number (on same or next line)
        imp_match = re.search(
            r"Impressions\s*\n?\s*([\d,]+)", full_text, re.IGNORECASE
        )
        if imp_match:
            impression_count = imp_match.group(1).replace(",", "")
        
        # METHOD 2: Try alternative patterns (for /p/ pages and other formats)
        if not registration_count:
            # Try "X Registered" pattern
            reg_match = re.search(
                r"([\d,]+)\s+Registered", full_text, re.IGNORECASE
            )
            if reg_match:
                registration_count = reg_match.group(1).replace(",", "")
        
        # METHOD 3: Look for "X Registration" or "X Registrations" pattern
        if not registration_count:
            reg_match = re.search(
                r"([\d,]+)\s+Registrations?", full_text, re.IGNORECASE
            )
            if reg_match:
                registration_count = reg_match.group(1).replace(",", "")
        
        if not impression_count:
            # Try "X Impressions" pattern  
            imp_match = re.search(
                r"([\d,]+)\s+Impressions?", full_text, re.IGNORECASE
            )
            if imp_match:
                impression_count = imp_match.group(1).replace(",", "")
        
        # Note: Some pages (/p/ URLs) may not have these stats at all
        return registration_count, impression_count

    def extract_about_content(self, soup):
        """Extract about section content as plain text"""
        # Try to find the specific div
        about_div = soup.find("div", class_="app-competition-about-form")
        if about_div:
            # Extract text and clean it up
            text = about_div.get_text(separator="\n", strip=True)
            # Remove excessive newlines
            text = re.sub(r"\n\s*\n+", "\n\n", text)
            return text.strip()

        # Try alternative selectors with more patterns
        selectors = [
            ("div", {"class_": lambda x: x and "about_game" in str(x)}),
            (
                "div",
                {
                    "class_": lambda x: x
                    and "about" in str(x).lower()
                    and "tab" in str(x).lower()
                },
            ),
            ("div", {"id": "tab-detail"}),
            ("div", {"id": "about"}),
            ("div", {"class_": "about-section"}),
            ("div", {"class_": "description"}),
            ("section", {"class_": "about"}),
            ("div", {"class_": "competition-details"}),
        ]

        for tag, attrs in selectors:
            element = soup.find(tag, **attrs)
            if element:
                # Extract text and clean it up
                text = element.get_text(separator="\n", strip=True)
                # Remove excessive newlines
                text = re.sub(r"\n\s*\n+", "\n\n", text)
                return text.strip()

        # If still nothing, try to find the largest content div
        all_divs = soup.find_all(
            "div", class_=lambda x: x and "detail" in str(x).lower()
        )
        if all_divs:
            largest = max(all_divs, key=lambda x: len(str(x)))
            if len(str(largest)) > 500:  # Only if substantial content
                # Extract text and clean it up
                text = largest.get_text(separator="\n", strip=True)
                # Remove excessive newlines
                text = re.sub(r"\n\s*\n+", "\n\n", text)
                return text.strip()

        return ""

    def extract_organizer_contact(self, soup):
        """Extract organizer contact information from the specific dates-and-contacts section"""
        contacts = []
        
        # Unstop's own contact numbers to exclude
        unstop_numbers = [
            '9311777388',  # Unstop support
            '93117 77388',
            '+91-9311777388',
            '+919311777388',
        ]
        
        # PRIORITY 1: Target the specific XPath component: app-dates-and-contacts
        dates_contacts_section = soup.find('app-dates-and-contacts')
        if dates_contacts_section:
            # Look for the contact information div (usually the second div)
            contact_divs = dates_contacts_section.find_all('div', recursive=False)
            
            # Try to get the second div which typically contains contact info
            if len(contact_divs) >= 2:
                contact_section = contact_divs[1]
                contact_text = contact_section.get_text(separator="\n", strip=True)
            else:
                # Fallback to all text in the section
                contact_text = dates_contacts_section.get_text(separator="\n", strip=True)
            
            # Extract structured contact information
            lines = contact_text.split('\n')
            for line in lines:
                line = line.strip()
                if not line or len(line) < 5:
                    continue
                
                # Skip headers and generic text
                if line.lower() in ['contact', 'contacts', 'contact information', 'organizer contact', 'contact the organisers', 'send queries to organizers', 'contact the organizers']:
                    continue
                
                # Check if it's an Unstop support number
                is_unstop_number = False
                for unstop_num in unstop_numbers:
                    if unstop_num.replace('-', '').replace('+', '').replace(' ', '') in line.replace('-', '').replace('+', '').replace(' ', ''):
                        is_unstop_number = True
                        break
                
                if is_unstop_number:
                    continue
                
                # Look for email patterns
                if '@' in line and len(line) < 150:
                    # Exclude common non-contact patterns
                    if not any(x in line.lower() for x in ['@unstop.com', '@example.com', 'noreply', 'no-reply']):
                        contacts.append(line)
                
                # Look for phone patterns (but not Unstop's)
                elif re.search(r'[\+\d][\d\s\-\(\)]{8,}', line):
                    contacts.append(line)
                
                # Look for name: value patterns (like "Contact Person: John Doe")
                elif ':' in line and len(line) < 150:
                    if any(keyword in line.lower() for keyword in ['contact', 'email', 'phone', 'mobile', 'call', 'name', 'person']):
                        contacts.append(line)
        
        # PRIORITY 2: Look for tab-dates section with id
        if not contacts:
            tab_dates = soup.find('div', id='tab-dates')
            if tab_dates:
                dates_contacts = tab_dates.find('app-dates-and-contacts')
                if dates_contacts:
                    # Get all divs within app-dates-and-contacts
                    divs = dates_contacts.find_all('div', recursive=False)
                    if len(divs) >= 2:
                        contact_div = divs[1]
                        text = contact_div.get_text(separator="\n", strip=True)
                        
                        for line in text.split('\n'):
                            line = line.strip()
                            if line and len(line) > 5 and len(line) < 150:
                                if '@' in line or re.search(r'[\d\-\+\(\)]{8,}', line) or ':' in line:
                                    if not any(x in line.lower() for x in ['@unstop.com', 'noreply']):
                                        contacts.append(line)
        
        # PRIORITY 3: Look for contact sections with specific classes
        if not contacts:
            contact_sections = soup.find_all(
                ['div', 'section'],
                class_=lambda x: x and any(
                    term in str(x).lower()
                    for term in ['contact', 'organizer-contact', 'organiser-contact']
                )
            )
            
            for section in contact_sections:
                text = section.get_text(separator="\n", strip=True)
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line or len(line) < 5 or len(line) > 150:
                        continue
                    
                    # Skip headers
                    if line.lower() in ['contact', 'contacts', 'contact information']:
                        continue
                    
                    # Extract relevant contact info
                    if '@' in line or re.search(r'[\+\d][\d\s\-\(\)]{8,}', line):
                        if not any(x in line.lower() for x in ['@unstop.com', '@example.com', 'noreply']):
                            if line not in contacts:
                                contacts.append(line)
        
        # Clean and format the output
        if contacts:
            # Remove duplicates while preserving order
            seen = set()
            unique_contacts = []
            for contact in contacts:
                normalized = re.sub(r'\s+', ' ', contact.lower())
                if normalized not in seen:
                    seen.add(normalized)
                    unique_contacts.append(contact)
            
            return "\n".join(unique_contacts[:15])  # Return up to 15 contact entries
        
        return ""

    def extract_important_dates(self, soup):
        """Extract important dates, stages, and timeline from competition-round-form"""
        dates_info = []
        seen = set()
        
        # PRIORITY 1: Look for the specific competition round form section
        competition_round = soup.find('app-competition-round-form')
        if competition_round:
            # Look for round/stage containers
            rounds = competition_round.find_all(['div', 'li'], 
                class_=lambda x: x and any(term in str(x).lower() for term in ['round', 'stage', 'phase']))
            
            for round_div in rounds:
                # Try to get round name/title
                round_title = round_div.find(['h3', 'h4', 'h5', 'strong', 'b'])
                title_text = round_title.get_text(strip=True) if round_title else ""
                
                # Get all text from this round
                full_text = round_div.get_text(separator=" | ", strip=True)
                
                # Split by common separators
                parts = re.split(r'\|', full_text)
                
                for part in parts:
                    part = part.strip()
                    if len(part) < 10 or len(part) > 300:
                        continue
                    
                    # Must contain a date
                    if re.search(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+[\d:,\s]*\d{2}', part, re.IGNORECASE):
                        # Normalize for duplicate checking
                        normalized = re.sub(r'\s+', ' ', part.lower())
                        if normalized not in seen:
                            seen.add(normalized)
                            dates_info.append(part)
        
        # PRIORITY 2: Look for app-explore-opportunity-viewer section
        if not dates_info:
            opportunity_viewer = soup.find('app-explore-opportunity-viewer')
            if opportunity_viewer:
                date_sections = opportunity_viewer.find_all(['div', 'li', 'span'])
                for section in date_sections:
                    text = section.get_text(separator=" ", strip=True)
                    if text and 10 < len(text) < 300:
                        if re.search(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', text, re.IGNORECASE):
                            normalized = re.sub(r'\s+', ' ', text.lower())
                            if normalized not in seen:
                                seen.add(normalized)
                                dates_info.append(text)
        
        # PRIORITY 3: Look for structured sections with timeline/round classes
        if not dates_info:
            date_containers = soup.find_all(['div', 'section', 'ul'], 
                class_=lambda x: x and any(term in str(x).lower() for term in [
                    'round', 'stage', 'timeline', 'deadline', 'schedule'
                ]))
            
            for container in date_containers:
                items = container.find_all(['div', 'li', 'p'])
                for item in items:
                    text = item.get_text(separator=" ", strip=True)
                    if 10 < len(text) < 300:
                        if re.search(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', text, re.IGNORECASE):
                            if any(keyword in text.lower() for keyword in [
                                'start', 'end', 'registration', 'submission', 'deadline', 
                                'result', 'announcement', 'round', 'stage', 'phase'
                            ]):
                                normalized = re.sub(r'\s+', ' ', text.lower())
                                if normalized not in seen:
                                    seen.add(normalized)
                                    dates_info.append(text)
        
        # FALLBACK: General search with strict criteria
        if not dates_info:
            all_elements = soup.find_all(['div', 'p', 'li', 'span'])
            
            for element in all_elements:
                text = element.get_text(separator=" ", strip=True)
                
                if not text or len(text) < 10 or len(text) > 300:
                    continue
                
                # Must contain a date pattern
                if not re.search(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+[\d:,\s]*\d{2}', text, re.IGNORECASE):
                    continue
                
                # Must contain a keyword
                if not any(keyword in text.lower() for keyword in [
                    'registration', 'submission', 'deadline', 'start', 'end',
                    'result', 'announcement', 'round', 'stage', 'phase'
                ]):
                    continue
                
                # Avoid duplicates
                normalized = re.sub(r'\s+', ' ', text.lower())
                if normalized not in seen:
                    seen.add(normalized)
                    dates_info.append(text)
        
        if dates_info:
            # Clean and format the output
            cleaned_dates = []
            for date_entry in dates_info[:20]:
                # Remove excessive whitespace
                cleaned = re.sub(r'\s+', ' ', date_entry).strip()
                if cleaned:
                    cleaned_dates.append(cleaned)
            
            return "\n".join(cleaned_dates)
        
        return ""

    def extract_official_website(self, soup):
        """Extract official website link if available"""
        
        # Look for links with "official", "website", "homepage" text
        official_links = soup.find_all('a', href=True, string=lambda x: x and any(
            term in str(x).lower() 
            for term in ['official website', 'website', 'homepage', 'visit site', 'know more']
        ))
        
        for link in official_links:
            href = link.get('href', '')
            # Exclude unstop.com links and social media
            if href and 'unstop.com' not in href.lower():
                if not any(social in href.lower() for social in [
                    'facebook.com', 'twitter.com', 'linkedin.com', 
                    'instagram.com', 'youtube.com', 'discord.com'
                ]):
                    if href.startswith('http'):
                        return href
                    elif href.startswith('/'):
                        continue  # Skip relative links
        
        # Look for links in organizer/contact sections
        organizer_sections = soup.find_all(
            ['div', 'section', 'p'],
            class_=lambda x: x and any(
                term in str(x).lower() 
                for term in ['organizer', 'organiser', 'contact', 'about']
            )
        )
        
        for section in organizer_sections:
            links = section.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                # Look for non-social media external links
                if href and href.startswith('http') and 'unstop.com' not in href.lower():
                    if not any(social in href.lower() for social in [
                        'facebook.com', 'twitter.com', 'linkedin.com', 
                        'instagram.com', 'youtube.com', 'discord.com', 'telegram'
                    ]):
                        # Check if it looks like a proper website
                        if '.' in href and len(href) > 10:
                            return href
        
        # Look for external links in the about section
        all_links = soup.find_all('a', href=True)
        external_links = []
        
        for link in all_links:
            href = link.get('href', '')
            if href and href.startswith('http') and 'unstop.com' not in href.lower():
                if not any(social in href.lower() for social in [
                    'facebook.com', 'twitter.com', 'linkedin.com', 
                    'instagram.com', 'youtube.com', 'discord.com', 'telegram',
                    'github.com', 'reddit.com', 'whatsapp', 'maps.google'
                ]):
                    # Prioritize .com, .org, .edu, .in domains
                    if any(ext in href for ext in ['.com', '.org', '.edu', '.in', '.net']):
                        external_links.append(href)
        
        # Return the first good external link
        if external_links:
            return external_links[0]
        
        return ""

    def scrape_with_selenium(self, headless, limit):
        """Scrape using Selenium (requires Chrome/Chromium)"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except ImportError:
            self.stdout.write(self.style.ERROR("Selenium not properly configured"))
            return

        # Setup Selenium WebDriver
        chrome_options = Options()
        
        # Use existing Chromium profile from config
        chrome_options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
        chrome_options.add_argument(f"--profile-directory={PROFILE_NAME}")
        
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument(f"user-agent={USER_AGENT}")
        chrome_options.binary_location = BROWSER_BINARY

        driver = webdriver.Chrome(options=chrome_options)

        try:
            # Get competition list
            competition_urls = self.get_competition_urls_selenium(driver, limit)
            self.stdout.write(
                self.style.SUCCESS(f"Found {len(competition_urls)} competitions")
            )

            # Scrape each competition
            for idx, url in enumerate(competition_urls, 1):
                self.stdout.write(f"Scraping {idx}/{len(competition_urls)}: {url}")
                try:
                    self.scrape_competition_selenium(driver, url)
                    time.sleep(2)  # Be respectful to the server
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error scraping {url}: {str(e)}")
                    )

        finally:
            driver.quit()

    def get_competition_urls_selenium(self, driver, limit=None):
        """Get all competition URLs using Selenium"""
        urls = []
        base_url = "https://unstop.com/competitions"

        driver.get(base_url)
        time.sleep(5)  # Wait for page to load

        # Scroll to load more content
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scrolls = 10 if limit else 20

        while scroll_attempts < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            scroll_attempts += 1

            self.stdout.write(f"Scrolling... attempt {scroll_attempts}")

        # Extract competition URLs
        soup = BeautifulSoup(driver.page_source, "html.parser")

        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            if "/competitions/" in href:
                if href.startswith("/"):
                    full_url = "https://unstop.com" + href
                elif href.startswith("http"):
                    full_url = href
                else:
                    continue

                clean_url = full_url.split("?")[0]
                if clean_url not in urls and "unstop.com" in clean_url:
                    urls.append(clean_url)

                    if limit and len(urls) >= limit:
                        return urls

        return urls

    def scrape_competition_selenium(self, driver, url):
        """Scrape individual competition page using Selenium"""
        driver.get(url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extract data using the same extraction methods
        name = self.extract_name(soup)
        organizer = self.extract_organizer(soup)
        registration_count, impression_count = self.extract_registered_count(soup)
        about_content = self.extract_about_content(soup)
        organizer_contact = self.extract_organizer_contact(soup)
        important_dates = self.extract_important_dates(soup)
        official_website = self.extract_official_website(soup)

        # Save to database
        competition, created = Competition.objects.update_or_create(
            url=url,
            defaults={
                "name": name or "Unknown",
                "organizer": organizer,
                "registered_count": registration_count,
                "registration_count": registration_count,
                "impression_count": impression_count,
                "about_content": about_content,
                "organizer_contact": organizer_contact,
                "important_dates": important_dates,
                "official_website": official_website,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"✓ Created: {name}"))
        else:
            self.stdout.write(self.style.WARNING(f"↻ Updated: {name}"))


    def scrape_from_file(self, filename, skip_existing=True, limit=None, concurrent_workers=1):
        """Scrape competitions from a file containing URLs (supports concurrent scraping)"""
        try:
            with open(filename, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            # Filter only /competitions/ URLs
            competition_urls = [url for url in urls if '/competitions/' in url]
            
            self.stdout.write(f"Loaded {len(competition_urls)} competition URLs from {filename}")
            
            if skip_existing:
                # Filter out already scraped URLs
                existing_urls = set(Competition.objects.values_list('url', flat=True))
                new_urls = [url for url in competition_urls if url not in existing_urls]
                self.stdout.write(f"After filtering: {len(new_urls)} new competitions to scrape")
                competition_urls = new_urls
            
            if limit:
                competition_urls = competition_urls[:limit]
                self.stdout.write(f"Limited to: {len(competition_urls)} competitions")
            
            if not competition_urls:
                self.stdout.write(self.style.WARNING("No URLs to scrape!"))
                return
            
            # Concurrent or sequential scraping
            if concurrent_workers > 1:
                self._scrape_concurrent(competition_urls, concurrent_workers)
            else:
                self._scrape_sequential(competition_urls)
                    
            self.stdout.write(self.style.SUCCESS(f"\n✓ Completed! Processed {len(competition_urls)} competitions"))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {filename}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading file: {str(e)}"))
    
    def _scrape_sequential(self, urls):
        """Scrape URLs one by one (original behavior)"""
        for idx, url in enumerate(urls, 1):
            self.stdout.write(f"\n[{idx}/{len(urls)}] Processing: {url}")
            try:
                self._process_single_competition(url, idx, len(urls))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))
    
    def _scrape_concurrent(self, urls, workers):
        """Scrape URLs concurrently using ThreadPoolExecutor"""
        self.stdout.write(f"⚡ Starting {workers} concurrent workers...")
        
        # Thread-safe counters
        self.success_count = 0
        self.error_count = 0
        self.lock = threading.Lock()
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self._process_single_competition_concurrent, url, idx, len(urls)): url 
                for idx, url in enumerate(urls, 1)
            }
            
            # Process completed tasks
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    future.result()
                except Exception as e:
                    with self.lock:
                        self.error_count += 1
                    self.stdout.write(self.style.ERROR(f"✗ Failed: {url[:60]}... - {str(e)[:100]}"))
        
        # Final summary
        self.stdout.write(self.style.SUCCESS(f"\n✓ Success: {self.success_count}"))
        if self.error_count > 0:
            self.stdout.write(self.style.WARNING(f"✗ Errors: {self.error_count}"))
    
    def _process_single_competition(self, url, idx, total):
        """Process a single competition (for sequential scraping)"""
        # Extract basic info and scrape page
        about_content, organizer_contact, official_website = (
            self.scrape_competition_page(url)
        )
        
        # Try to extract name from URL
        name = url.split('/')[-1].replace('-', ' ').title()
        
        # Save to database
        competition, created = Competition.objects.update_or_create(
            url=url,
            defaults={
                "name": name,
                "organizer": "",  # Will be in about_content
                "registration_count": "",
                "impression_count": "",
                "about_content": about_content,
                "organizer_contact": organizer_contact,
                "important_dates": "",
                "official_website": official_website,
                "prizes": "",
            },
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created: {name}"))
        else:
            self.stdout.write(self.style.WARNING(f"  ↻ Updated: {name}"))
    
    def _process_single_competition_concurrent(self, url, idx, total):
        """Process a single competition (for concurrent scraping)"""
        try:
            # Extract basic info and scrape page
            about_content, organizer_contact, official_website = (
                self.scrape_competition_page(url)
            )
            
            # Try to extract name from URL
            name = url.split('/')[-1].replace('-', ' ').title()
            
            # Save to database (thread-safe with Django ORM)
            competition, created = Competition.objects.update_or_create(
                url=url,
                defaults={
                    "name": name,
                    "organizer": "",  # Will be in about_content
                    "registration_count": "",
                    "impression_count": "",
                    "about_content": about_content,
                    "organizer_contact": organizer_contact,
                    "important_dates": "",
                    "official_website": official_website,
                    "prizes": "",
                },
            )
            
            with self.lock:
                self.success_count += 1
                status = "✓ Created" if created else "↻ Updated"
                self.stdout.write(f"[{self.success_count + self.error_count}/{total}] {status}: {name[:60]}")
                
        except Exception as e:
            raise  # Re-raise to be caught by executor
