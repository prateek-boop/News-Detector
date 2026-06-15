import time
import re
import requests
import json
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from scraper.models import DevfolioHackathon
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from browser_config import USER_DATA_DIR, PROFILE_NAME, BROWSER_BINARY, USER_AGENT


class Command(BaseCommand):
    help = """
    Scrape hackathons from Devfolio using their API.
    
    Fetches hackathons from open, past, and upcoming categories.
    Extracts comprehensive data including dates, prizes, themes, and contact info.
    
    USAGE MODES:
    
    1. Scrape specific status:
       python manage.py scrape_devfolio --status open
       python manage.py scrape_devfolio --status past
       python manage.py scrape_devfolio --status upcoming
    
    2. Scrape all statuses:
       python manage.py scrape_devfolio --status all
    
    3. Scrape from file (for detailed page scraping):
       python manage.py scrape_devfolio --from-file devfolio_urls.txt
    
    EXAMPLES:
    
      # Scrape open hackathons (API-based, fast)
      python manage.py scrape_devfolio --status open
      
      # Scrape all hackathons (API-based)
      python manage.py scrape_devfolio --status all
      
      # Scrape past hackathons with limit
      python manage.py scrape_devfolio --status past --limit 50
      
      # Force rescrape existing hackathons
      python manage.py scrape_devfolio --status all --force-rescrape
      
      # Scrape from URL file (for detailed data)
      python manage.py scrape_devfolio --from-file devfolio_urls.txt
    
    OPTIONS:
      --status STATUS      Scrape 'open', 'past', 'upcoming', or 'all' (default: all)
      --limit N            Scrape only N hackathons per status
      --skip-existing      Skip already scraped hackathons (default: True)
      --force-rescrape     Rescrape even if already in database
      --from-file FILE     Read URLs from file for detailed scraping
    
    EXTRACTED DATA:
      - Name, organizer, status (open/past/upcoming)
      - Participants count, projects count
      - About content, dates (start/end)
      - Location, mode (online/offline/hybrid)
      - Prizes, themes, contact info
      - Official website
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--status",
            type=str,
            choices=['open', 'past', 'upcoming', 'all'],
            default='all',
            help="Status of hackathons to scrape (default: all)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of hackathons to scrape per status",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            default=False,
            help="Skip hackathons already in database (default: False)",
        )
        parser.add_argument(
            "--force-rescrape",
            action="store_true",
            help="Rescrape all hackathons even if already in database",
        )
        parser.add_argument(
            "--from-file",
            type=str,
            help="Read URLs from file (one URL per line)",
        )

    def handle(self, *args, **options):
        status = options["status"]
        limit = options["limit"]
        skip_existing = options["skip_existing"] and not options["force_rescrape"]
        from_file = options.get("from_file")

        self.stdout.write(self.style.SUCCESS("Starting Devfolio hackathon scraper..."))
        
        # Handle file-based scraping (detailed page scraping)
        if from_file:
            self.scrape_from_file(from_file, skip_existing, limit)
            return
        
        if skip_existing:
            self.stdout.write(self.style.SUCCESS("Skip existing: Enabled"))
        else:
            self.stdout.write(self.style.WARNING("Skip existing: Disabled (will rescrape all)"))

        # Determine which statuses to scrape
        if status == 'all':
            statuses = ['open', 'upcoming', 'past']
        else:
            statuses = [status]

        self.stdout.write(f"Will scrape statuses: {', '.join(statuses)}")

        # Use API-based scraping (much faster and more reliable)
        try:
            for current_status in statuses:
                self.stdout.write(self.style.SUCCESS(f"\n{'='*60}"))
                self.stdout.write(self.style.SUCCESS(f"Scraping {current_status.upper()} hackathons"))
                self.stdout.write(self.style.SUCCESS(f"{'='*60}"))
                
                self.scrape_status_api(current_status, limit, skip_existing)

            self.stdout.write(self.style.SUCCESS("\n✓ Devfolio scraping completed!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())

    def scrape_status_api(self, status, limit, skip_existing):
        """Scrape hackathons using Devfolio's API"""
        # Map status to API type
        status_map = {
            'open': 'application_open',
            'upcoming': 'upcoming',
            'past': 'past'
        }
        
        api_type = status_map.get(status, 'application_open')
        api_url = "https://api.devfolio.co/api/search/hackathons"
        
        # Fetch all hackathons from API
        all_hackathons = []
        page_size = 50
        from_index = 0
        
        while True:
            payload = {
                "type": api_type,
                "from": from_index,
                "size": page_size
            }
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': USER_AGENT
            }
            
            try:
                response = requests.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                hits = data.get('hits', {}).get('hits', [])
                total = data.get('hits', {}).get('total', {}).get('value', 0)
                
                if not hits:
                    break
                
                all_hackathons.extend(hits)
                self.stdout.write(f"Fetched {len(all_hackathons)}/{total} hackathons from API...")
                
                if len(all_hackathons) >= total:
                    break
                    
                from_index += page_size
                time.sleep(0.5)  # Be respectful
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"API error: {str(e)}"))
                break
        
        self.stdout.write(f"Found {len(all_hackathons)} hackathons via API")
        
        if limit:
            all_hackathons = all_hackathons[:limit]
            self.stdout.write(f"Limited to: {len(all_hackathons)} hackathons")
        
        # Process each hackathon
        saved_count = 0
        skipped_count = 0
        updated_count = 0
        
        for idx, hack_data in enumerate(all_hackathons, 1):
            try:
                source = hack_data.get('_source', {})
                slug = source.get('slug')
                url = f"https://{slug}.devfolio.co/overview"
                
                # Check if exists
                if skip_existing and DevfolioHackathon.objects.filter(url=url).exists():
                    skipped_count += 1
                    continue
                
                self.stdout.write(f"[{idx}/{len(all_hackathons)}] Processing: {source.get('name', slug)}")
                
                # Save hackathon from API data
                created = self.save_hackathon_from_api(source, status)
                if created:
                    saved_count += 1
                else:
                    updated_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Error processing hackathon: {str(e)}"))
                import traceback
                self.stdout.write(traceback.format_exc())
        
        self.stdout.write(self.style.SUCCESS(f"\n✓ Saved: {saved_count}, Updated: {updated_count}, Skipped: {skipped_count}"))

    def save_hackathon_from_api(self, source, status):
        """Save hackathon from API response data"""
        slug = source.get('slug')
        url = f"https://{slug}.devfolio.co/overview"
        settings = source.get('hackathon_setting', {})
        
        # Extract data
        name = slug.replace('-', ' ').title()  # Basic name from slug
        
        # Extract organizer - use hosted_by if available, otherwise use the hackathon name itself
        # DO NOT use city as organizer
        organizer = source.get('hosted_by')
        if not organizer:
            # Use the hackathon name as organizer (it's usually the organizing entity)
            organizer = name
        
        # Extract location and mode
        location = []
        if source.get('city'):
            location.append(source.get('city'))
        if source.get('state'):
            location.append(source.get('state'))
        if source.get('country'):
            location.append(source.get('country'))
        
        location_str = ', '.join(location) if location else None
        mode = 'online' if source.get('is_online') else 'offline'
        
        # Dates
        starts_at = source.get('starts_at')
        ends_at = source.get('ends_at')
        
        # Important dates
        important_dates = []
        if settings.get('reg_starts_at'):
            important_dates.append(f"Registration starts: {settings['reg_starts_at']}")
        if settings.get('reg_ends_at'):
            important_dates.append(f"Registration ends: {settings['reg_ends_at']}")
        if starts_at:
            important_dates.append(f"Event starts: {starts_at}")
        if ends_at:
            important_dates.append(f"Event ends: {ends_at}")
        
        # Themes and prizes
        themes = ', '.join([t.get('name', '') for t in source.get('themes', [])])
        
        # Extract prizes from sponsor tiers
        prizes = []
        for tier in source.get('sponsor_tiers', []):
            tier_name = tier.get('name', '')
            if tier_name and tier.get('sponsors'):
                prizes.append(f"{tier_name} sponsors: {len(tier['sponsors'])}")
        
        # Contact and Social Links (comprehensive collection)
        contact_parts = []
        
        # Email
        if settings.get('contact_email'):
            contact_parts.append(f"Email: {settings['contact_email']}")
        
        # Social Media Links
        if settings.get('twitter'):
            contact_parts.append(f"Twitter: {settings['twitter']}")
        
        if settings.get('linkedin'):
            contact_parts.append(f"LinkedIn: {settings['linkedin']}")
        
        if settings.get('discord'):
            contact_parts.append(f"Discord: {settings['discord']}")
        
        if settings.get('telegram'):
            contact_parts.append(f"Telegram: {settings['telegram']}")
        
        if settings.get('facebook'):
            contact_parts.append(f"Facebook: {settings['facebook']}")
        
        if settings.get('instagram'):
            contact_parts.append(f"Instagram: {settings['instagram']}")
        
        if settings.get('youtube'):
            contact_parts.append(f"YouTube: {settings['youtube']}")
        
        if settings.get('github'):
            contact_parts.append(f"GitHub: {settings['github']}")
        
        # Website/social
        website = settings.get('site') or settings.get('linkedin') or settings.get('twitter')
        
        # Create or update
        hackathon, created = DevfolioHackathon.objects.update_or_create(
            url=url,
            defaults={
                'name': name,
                'organizer': organizer,
                'status': status,
                'participants_count': str(source.get('participants_count')) if source.get('participants_count') else None,
                'projects_count': str(source.get('projects_count')) if source.get('projects_count') else None,
                'about_content': None,  # Would need to scrape individual page
                'prizes': '\n'.join(prizes) if prizes else None,
                'themes': themes or None,
                'start_date': starts_at,
                'end_date': ends_at,
                'important_dates': '\n'.join(important_dates) if important_dates else None,
                'location': location_str,
                'mode': mode,
                'organizer_contact': '\n'.join(contact_parts) if contact_parts else None,
                'official_website': website,
            }
        )
        
        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"  ✓ {action}: {name}"))
        return created

    def scrape_from_file(self, filename, skip_existing, limit):
        """Scrape hackathons from a file containing URLs"""
        self.stdout.write(f"Reading URLs from: {filename}")
        
        try:
            with open(filename, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {filename}"))
            return
        
        self.stdout.write(f"Found {len(urls)} URLs in file")
        
        if skip_existing:
            existing_urls = set(DevfolioHackathon.objects.filter(
                url__in=urls
            ).values_list('url', flat=True))
            urls = [url for url in urls if url not in existing_urls]
            self.stdout.write(f"After filtering: {len(urls)} new URLs to scrape")
        
        if limit:
            urls = urls[:limit]
            self.stdout.write(f"Limited to: {len(urls)} URLs")
        
        # Setup Selenium for detailed scraping
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={USER_AGENT}")
        chrome_options.binary_location = BROWSER_BINARY
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            for idx, url in enumerate(urls, 1):
                self.stdout.write(f"\n[{idx}/{len(urls)}] Scraping: {url}")
                try:
                    # Determine status from URL or default to 'open'
                    status = 'open'
                    self.scrape_hackathon_page(driver, url, status)
                    time.sleep(2)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Error: {str(e)}"))
            
            self.stdout.write(self.style.SUCCESS("\n✓ File-based scraping completed!"))
        finally:
            if driver:
                driver.quit()

    def scrape_hackathon_page(self, driver, url, status):
        """Scrape individual hackathon page (detailed scraping)"""
        driver.get(url)
        time.sleep(4)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Check for 404 page
        page_text = soup.get_text().lower()
        if '404' in page_text or 'not found' in page_text or 'page not found' in page_text:
            title = soup.find('title')
            if title and '404' in title.get_text():
                self.stdout.write(self.style.WARNING(f"  ⚠ Skipped: 404 Not Found"))
                return
        
        # Extract data using detailed scraping methods
        name = self.extract_name(soup, url)
        organizer = self.extract_organizer(soup)
        participants_count = self.extract_participants_count(soup)
        projects_count = self.extract_projects_count(soup)
        about_content = self.extract_about_content(soup)
        start_date, end_date = self.extract_dates(soup)
        location = self.extract_location(soup)
        mode = self.extract_mode(soup)
        prizes = self.extract_prizes(soup)
        themes = self.extract_themes(soup)
        organizer_contact = self.extract_contact(soup)
        official_website = self.extract_official_website(soup)
        important_dates = self.extract_important_dates(soup)
        
        # Save to database
        hackathon, created = DevfolioHackathon.objects.update_or_create(
            url=url,
            defaults={
                'name': name,
                'organizer': organizer,
                'status': status,
                'participants_count': participants_count,
                'projects_count': projects_count,
                'about_content': about_content,
                'start_date': start_date,
                'end_date': end_date,
                'location': location,
                'mode': mode,
                'prizes': prizes,
                'themes': themes,
                'organizer_contact': organizer_contact,
                'official_website': official_website,
                'important_dates': important_dates,
            },
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created: {name}"))
        else:
            self.stdout.write(self.style.WARNING(f"  ↻ Updated: {name}"))

    def extract_name(self, soup, url):
        """Extract hackathon name"""
        # Try h1 tag first
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        # Try title tag
        title = soup.find('title')
        if title:
            text = title.get_text(strip=True)
            # Remove " | Devfolio" suffix
            return text.replace(' | Devfolio', '').strip()
        
        # Fallback to URL
        return url.split('/')[-1].replace('-', ' ').title()

    def extract_organizer(self, soup):
        """Extract organizer name"""
        # Look for organizer information
        # This may vary, try multiple approaches
        
        # Try finding text like "Organized by"
        text = soup.get_text()
        match = re.search(r'Organized by\s+([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        match = re.search(r'Organizer[s]?:\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return ""

    def extract_participants_count(self, soup):
        """Extract participants count"""
        text = soup.get_text()
        
        # Look for patterns like "1,234 participants"
        match = re.search(r'([\d,]+)\s+participants?', text, re.IGNORECASE)
        if match:
            return match.group(1).replace(',', '')
        
        return ""

    def extract_projects_count(self, soup):
        """Extract projects submitted count"""
        text = soup.get_text()
        
        # Look for patterns like "567 projects"
        match = re.search(r'([\d,]+)\s+projects?', text, re.IGNORECASE)
        if match:
            return match.group(1).replace(',', '')
        
        return ""

    def extract_about_content(self, soup):
        """Extract about/description content"""
        # Look for about section
        about_section = soup.find(['section', 'div'], class_=lambda x: x and 'about' in str(x).lower())
        if about_section:
            return about_section.get_text(separator='\n', strip=True)
        
        # Try finding description meta tag
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content')
        
        # Look for paragraphs in main content
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = '\n\n'.join([p.get_text(strip=True) for p in paragraphs[:5] if len(p.get_text(strip=True)) > 50])
            if content:
                return content
        
        return ""

    def extract_dates(self, soup):
        """Extract start and end dates"""
        text = soup.get_text()
        
        # Look for date patterns
        # Common formats: "Jan 15 - Jan 17, 2025" or "15 Jan 2025 - 17 Jan 2025"
        date_pattern = r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})'
        dates = re.findall(date_pattern, text, re.IGNORECASE)
        
        if len(dates) >= 2:
            return dates[0], dates[1]
        elif len(dates) == 1:
            return dates[0], ""
        
        return "", ""

    def extract_location(self, soup):
        """Extract location"""
        text = soup.get_text()
        
        # Look for location patterns
        match = re.search(r'Location[:\s]+([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Look for city/country names
        match = re.search(r'(?:at|in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', text)
        if match:
            location = match.group(1).strip()
            if len(location) < 50:
                return location
        
        return ""

    def extract_mode(self, soup):
        """Extract mode (online/offline/hybrid)"""
        text = soup.get_text().lower()
        
        if 'hybrid' in text:
            return 'hybrid'
        elif 'online' in text or 'virtual' in text:
            return 'online'
        elif 'offline' in text or 'in-person' in text or 'on-site' in text:
            return 'offline'
        
        return ""

    def extract_prizes(self, soup):
        """Extract prize information"""
        # Look for prize section
        prize_section = soup.find(['section', 'div'], class_=lambda x: x and 'prize' in str(x).lower())
        if prize_section:
            return prize_section.get_text(separator='\n', strip=True)
        
        # Look for prize amounts in text
        text = soup.get_text()
        prize_matches = re.findall(r'₹[\d,]+|INR[\d,]+|\$[\d,]+|USD[\d,]+', text)
        if prize_matches:
            return '\n'.join(prize_matches[:10])
        
        return ""

    def extract_themes(self, soup):
        """Extract hackathon themes/tracks"""
        # Look for themes section
        theme_section = soup.find(['section', 'div'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['theme', 'track', 'category']
        ))
        if theme_section:
            # Try to find list items
            items = theme_section.find_all(['li', 'span', 'div'])
            themes = [item.get_text(strip=True) for item in items if 5 < len(item.get_text(strip=True)) < 100]
            if themes:
                return '\n'.join(themes[:15])
        
        return ""

    def extract_contact(self, soup):
        """Extract organizer contact information and all social links"""
        contacts = []
        
        # Find all links in the page
        all_links = soup.find_all('a', href=True)
        
        # Social media patterns
        social_patterns = {
            'Email': r'mailto:([\w\.-]+@[\w\.-]+\.\w+)',
            'Twitter': r'(?:twitter\.com|x\.com)/[\w\-]+',
            'LinkedIn': r'linkedin\.com/(?:company|in)/[\w\-]+',
            'Discord': r'discord\.(?:gg|com)/[\w\-]+',
            'Telegram': r't\.me/[\w\-]+',
            'Facebook': r'facebook\.com/[\w\-\.]+',
            'Instagram': r'instagram\.com/[\w\-\.]+',
            'YouTube': r'youtube\.com/[\w\-/@]+',
            'GitHub': r'github\.com/[\w\-]+',
        }
        
        found_socials = {}
        
        # Extract from href attributes
        for link in all_links:
            href = link.get('href', '')
            
            # Check each social pattern
            for platform, pattern in social_patterns.items():
                if platform == 'Email' and href.startswith('mailto:'):
                    match = re.search(social_patterns['Email'], href)
                    if match and platform not in found_socials:
                        found_socials[platform] = match.group(1)
                elif re.search(pattern, href, re.IGNORECASE):
                    if platform not in found_socials:
                        # Clean up the URL
                        if not href.startswith('http'):
                            href = 'https://' + href
                        found_socials[platform] = href
        
        # Also search in text for emails and links
        text = soup.get_text()
        
        # Extract emails from text if not found in links
        if 'Email' not in found_socials:
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
            # Filter out common non-contact emails
            emails = [e for e in emails if not any(x in e.lower() for x in ['example.com', 'devfolio.co', 'noreply', 'test@'])]
            if emails:
                found_socials['Email'] = emails[0]
        
        # Extract phone numbers
        phones = re.findall(r'(?:\+\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', text)
        if phones:
            found_socials['Phone'] = phones[0]
        
        # Format the output
        for platform in ['Email', 'Phone', 'Twitter', 'LinkedIn', 'Discord', 'Telegram', 'Facebook', 'Instagram', 'YouTube', 'GitHub']:
            if platform in found_socials:
                contacts.append(f"{platform}: {found_socials[platform]}")
        
        return '\n'.join(contacts) if contacts else ""

    def extract_official_website(self, soup):
        """Extract official website link"""
        # Look for external links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            # Skip devfolio.co links and common social media
            if href.startswith('http') and 'devfolio.co' not in href:
                if not any(social in href.lower() for social in [
                    'facebook.com', 'twitter.com', 'linkedin.com', 
                    'instagram.com', 'youtube.com', 'discord.com',
                    'github.com', 'telegram'
                ]):
                    # Likely an official website
                    if '.' in href and len(href) > 10:
                        return href
        
        return ""

    def extract_important_dates(self, soup):
        """Extract all important dates and deadlines"""
        dates_info = []
        
        # Look for dates section
        dates_section = soup.find(['section', 'div'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['date', 'timeline', 'schedule', 'deadline']
        ))
        
        if dates_section:
            text = dates_section.get_text(separator='\n', strip=True)
            lines = text.split('\n')
            
            for line in lines:
                if re.search(r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', line, re.IGNORECASE):
                    if len(line) < 200:
                        dates_info.append(line)
        
        return '\n'.join(dates_info[:10]) if dates_info else ""

    def scrape_from_file(self, filename, skip_existing=True, limit=None):
        """Scrape Devfolio hackathons from a file containing URLs"""
        try:
            with open(filename, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            # Filter only devfolio.co URLs
            devfolio_urls = [url for url in urls if 'devfolio.co' in url and '/hackathons/' in url]
            
            self.stdout.write(f"Loaded {len(devfolio_urls)} Devfolio URLs from {filename}")
            
            if skip_existing:
                existing_urls = set(DevfolioHackathon.objects.values_list('url', flat=True))
                new_urls = [url for url in devfolio_urls if url not in existing_urls]
                self.stdout.write(f"After filtering: {len(new_urls)} new hackathons to scrape")
                devfolio_urls = new_urls
            
            if limit:
                devfolio_urls = devfolio_urls[:limit]
                self.stdout.write(f"Limited to: {len(devfolio_urls)} hackathons")
            
            if not devfolio_urls:
                self.stdout.write(self.style.WARNING("No URLs to scrape"))
                return
            
            # Setup Selenium
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"user-agent={USER_AGENT}")
            chrome_options.binary_location = BROWSER_BINARY
            
            driver = None
            try:
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Scrape each URL
                for idx, url in enumerate(devfolio_urls, 1):
                    self.stdout.write(f"\n[{idx}/{len(devfolio_urls)}] Scraping: {url}")
                    try:
                        self.scrape_hackathon_page(driver, url, "unknown")
                        time.sleep(2)
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  Error: {str(e)}"))
                        
                self.stdout.write(self.style.SUCCESS(f"\n✓ Completed! Processed {len(devfolio_urls)} hackathons"))
                
            finally:
                if driver:
                    driver.quit()
                    
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {filename}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error reading file: {str(e)}"))
