import time
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from scraper.models import Hackathon
import re
from browser_config import USER_DATA_DIR, PROFILE_NAME, BROWSER_BINARY, USER_AGENT


class Command(BaseCommand):
    help = """
    Update existing hackathons with latest data from Unstop.
    
    This command allows you to refresh/update data for specific hackathons
    without running a full scrape. Useful for updating outdated information.
    
    USAGE MODES:
    
    1. Update by URL:
       python manage.py update_unstop --url <hackathon-url>
    
    2. Update by ID:
       python manage.py update_unstop --id 5
    
    3. Update all hackathons:
       python manage.py update_unstop --all
    
    4. Update outdated only (missing contact/counts):
       python manage.py update_unstop --all --outdated-only
    
    EXAMPLES:
    
      # Update specific hackathon by URL
      python manage.py update_unstop --url https://unstop.com/hackathons/example-123
      
      # Update specific hackathon by database ID
      python manage.py update_unstop --id 42
      
      # Update all hackathons
      python manage.py update_unstop --all
      
      # Update only hackathons with missing contact info
      python manage.py update_unstop --all --outdated-only
      
      # Update first 20 outdated hackathons
      python manage.py update_unstop --all --outdated-only --limit 20
    
    OPTIONS:
      --all               Update all hackathons
      --url URL           URL of specific hackathon to update
      --id ID             Database ID of hackathon to update
      --outdated-only     Only update entries missing contact/count data
      --limit N           Limit to N hackathons (with --all)
    
    WHAT GETS UPDATED:
      - Registration count and impression count
      - About content
      - Organizer contact information
      - Important dates
      - Official website
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Update all hackathons in database",
        )
        parser.add_argument(
            "--url",
            type=str,
            help="Update specific hackathon by URL",
        )
        parser.add_argument(
            "--id",
            type=int,
            help="Update specific hackathon by ID",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of hackathons to update (when using --all)",
        )
        parser.add_argument(
            "--outdated-only",
            action="store_true",
            help="Only update hackathons with missing impression_count or registration_count",
        )
        parser.add_argument(
            "--headless",
            action="store_true",
            default=True,
            help="Run browser in headless mode (default: True)",
        )

    def handle(self, *args, **options):
        all_hackathons = options["all"]
        url = options["url"]
        hackathon_id = options["id"]
        limit = options["limit"]
        outdated_only = options["outdated_only"]
        headless = options.get("headless", True)

        self.stdout.write(self.style.SUCCESS("Starting Unstop hackathon updater..."))
        if headless:
            self.stdout.write("Running in HEADLESS mode")

        if url:
            # Update specific hackathon by URL
            try:
                hackathon = Hackathon.objects.get(url=url)
                self.update_hackathon(hackathon, headless)
            except Hackathon.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Hackathon with URL {url} not found"))
        elif hackathon_id:
            # Update specific hackathon by ID
            try:
                hackathon = Hackathon.objects.get(id=hackathon_id)
                self.update_hackathon(hackathon, headless)
            except Hackathon.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Hackathon with ID {hackathon_id} not found"))
        elif all_hackathons:
            # Update all or filtered hackathons
            if outdated_only:
                hackathons = Hackathon.objects.filter(
                    impression_count__isnull=True
                ) | Hackathon.objects.filter(
                    registration_count__isnull=True
                ) | Hackathon.objects.filter(
                    impression_count=""
                ) | Hackathon.objects.filter(
                    registration_count=""
                ) | Hackathon.objects.filter(
                    organizer_contact__isnull=True
                ) | Hackathon.objects.filter(
                    organizer_contact=""
                )
                self.stdout.write(
                    self.style.WARNING(
                        f"Found {hackathons.count()} hackathons with missing data"
                    )
                )
            else:
                hackathons = Hackathon.objects.all()
                self.stdout.write(
                    self.style.WARNING(f"Updating all {hackathons.count()} hackathons")
                )

            if limit:
                hackathons = hackathons[:limit]
                self.stdout.write(self.style.WARNING(f"Limited to {limit} hackathons"))

            total = hackathons.count()
            for idx, hackathon in enumerate(hackathons, 1):
                self.stdout.write(f"\n[{idx}/{total}] Updating: {hackathon.name}")
                try:
                    self.update_hackathon(hackathon, headless)
                    time.sleep(2)  # Be respectful to the server
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error updating {hackathon.url}: {str(e)}")
                    )
        else:
            self.stdout.write(
                self.style.ERROR(
                    "Please specify --all, --url <url>, or --id <id> to update hackathons"
                )
            )
            return

        self.stdout.write(self.style.SUCCESS("\nUpdate completed!"))

    def update_hackathon(self, hackathon, headless=True):
        """Update a single hackathon with latest data"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

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

        driver = None
        try:
            # Use webdriver-manager to handle ChromeDriver automatically
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Navigate to the hackathon page
            self.stdout.write(f"  Fetching: {hackathon.url}")
            driver.get(hackathon.url)

            # Wait for page to load
            time.sleep(5)

            # Get page source after JavaScript execution
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Extract updated data
            registration_count, impression_count = self.extract_counts(soup)
            about_content = self.extract_about_content(soup)
            organizer_contact = self.extract_organizer_contact(soup)
            important_dates = self.extract_important_dates(soup)
            official_website = self.extract_official_website(soup)

            # Update the hackathon
            updated_fields = []
            
            if registration_count:
                hackathon.registration_count = registration_count
                hackathon.registered_count = registration_count
                updated_fields.append("registration_count")
            
            if impression_count:
                hackathon.impression_count = impression_count
                updated_fields.append("impression_count")
            
            if about_content:
                hackathon.about_content = about_content
                updated_fields.append("about_content")
            
            if organizer_contact:
                hackathon.organizer_contact = organizer_contact
                updated_fields.append("organizer_contact")
            
            if important_dates:
                hackathon.important_dates = important_dates
                updated_fields.append("important_dates")
            
            if official_website:
                hackathon.official_website = official_website
                updated_fields.append("official_website")

            hackathon.save()

            if updated_fields:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ Updated: {', '.join(updated_fields)}"
                    )
                )
                if registration_count:
                    self.stdout.write(f"    Registration count: {registration_count}")
                if impression_count:
                    self.stdout.write(f"    Impression count: {impression_count}")
            else:
                self.stdout.write(self.style.WARNING("  - No new data found"))
            
            # Warn if counts weren't found (might be a /p/ page)
            if not registration_count and not impression_count:
                if '/p/' in hackathon.url:
                    self.stdout.write(self.style.WARNING("  ⚠ This appears to be a /p/ page - stats may not be available"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())
        finally:
            if driver:
                driver.quit()

    def extract_counts(self, soup):
        """Extract registration and impression counts"""
        registration_count = ""
        impression_count = ""

        full_text = soup.get_text()
        
        # METHOD 1: Look for "Registered" label followed by number (for /hackathons/ pages)
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
        # Return empty strings if not found
        return registration_count, impression_count

    def extract_about_content(self, soup):
        """Extract about section content as plain text"""
        # Try to find the specific div
        about_div = soup.find("div", class_="app-competition-about-form")
        if about_div:
            text = about_div.get_text(separator="\n", strip=True)
            text = re.sub(r"\n\s*\n+", "\n\n", text)
            return text.strip()

        # Try alternative selectors
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
        ]

        for tag, attrs in selectors:
            element = soup.find(tag, **attrs)
            if element:
                text = element.get_text(separator="\n", strip=True)
                text = re.sub(r"\n\s*\n+", "\n\n", text)
                return text.strip()

        return ""

    def extract_organizer_contact(self, soup):
        """Extract organizer contact information"""
        contacts = []
        
        # Unstop's own contact numbers to exclude
        unstop_numbers = [
            '9311777388',  # Unstop support
            '93117 77388',
            '+91-9311777388',
            '+919311777388',
        ]

        # Look for app-dates-and-contacts section
        dates_contacts_section = soup.find("app-dates-and-contacts")
        if dates_contacts_section:
            contact_divs = dates_contacts_section.find_all("div", recursive=False)

            if len(contact_divs) >= 2:
                contact_section = contact_divs[1]
                contact_text = contact_section.get_text(separator="\n", strip=True)
            else:
                contact_text = dates_contacts_section.get_text(
                    separator="\n", strip=True
                )

            lines = contact_text.split("\n")
            for line in lines:
                line = line.strip()
                if not line or len(line) < 5:
                    continue

                # Skip headers and generic text
                if line.lower() in [
                    "contact",
                    "contacts",
                    "contact information",
                    "organizer contact",
                    "contact the organisers",
                    "send queries to organizers",
                    "contact the organizers",
                ]:
                    continue

                # Check if it's an Unstop support number
                is_unstop_number = False
                for unstop_num in unstop_numbers:
                    if unstop_num.replace('-', '').replace('+', '').replace(' ', '') in line.replace('-', '').replace('+', '').replace(' ', ''):
                        is_unstop_number = True
                        break
                
                if is_unstop_number:
                    continue

                # Extract email addresses
                if "@" in line and len(line) < 150:
                    if not any(
                        x in line.lower()
                        for x in ["@unstop.com", "@example.com", "noreply", "no-reply"]
                    ):
                        contacts.append(line)

                # Extract phone numbers (but not Unstop's)
                elif re.search(r"[\+\d][\d\s\-\(\)]{8,}", line):
                    contacts.append(line)

                # Extract labeled contact info
                elif ":" in line and len(line) < 150:
                    if any(
                        keyword in line.lower()
                        for keyword in [
                            "contact",
                            "email",
                            "phone",
                            "mobile",
                            "call",
                            "name",
                            "person",
                        ]
                    ):
                        contacts.append(line)

        if contacts:
            seen = set()
            unique_contacts = []
            for contact in contacts:
                normalized = re.sub(r"\s+", " ", contact.lower())
                if normalized not in seen:
                    seen.add(normalized)
                    unique_contacts.append(contact)

            return "\n".join(unique_contacts[:15])

        return ""

    def extract_important_dates(self, soup):
        """Extract important dates and timeline"""
        dates_info = []
        seen = set()

        competition_round = soup.find("app-competition-round-form")
        if competition_round:
            rounds = competition_round.find_all(
                ["div", "li"],
                class_=lambda x: x
                and any(term in str(x).lower() for term in ["round", "stage", "phase"]),
            )

            for round_div in rounds:
                full_text = round_div.get_text(separator=" | ", strip=True)
                parts = re.split(r"\|", full_text)

                for part in parts:
                    part = part.strip()
                    if len(part) < 10 or len(part) > 300:
                        continue

                    if re.search(
                        r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+[\d:,\s]*\d{2}",
                        part,
                        re.IGNORECASE,
                    ):
                        normalized = re.sub(r"\s+", " ", part.lower())
                        if normalized not in seen:
                            seen.add(normalized)
                            dates_info.append(part)

        if dates_info:
            cleaned_dates = []
            for date_entry in dates_info[:20]:
                cleaned = re.sub(r"\s+", " ", date_entry).strip()
                if cleaned:
                    cleaned_dates.append(cleaned)

            return "\n".join(cleaned_dates)

        return ""

    def extract_official_website(self, soup):
        """Extract official website link"""
        official_links = soup.find_all(
            "a",
            href=True,
            string=lambda x: x
            and any(
                term in str(x).lower()
                for term in [
                    "official website",
                    "website",
                    "homepage",
                    "visit site",
                    "know more",
                ]
            ),
        )

        for link in official_links:
            href = link.get("href", "")
            if href and "unstop.com" not in href.lower():
                if not any(
                    social in href.lower()
                    for social in [
                        "facebook.com",
                        "twitter.com",
                        "linkedin.com",
                        "instagram.com",
                        "youtube.com",
                        "discord.com",
                    ]
                ):
                    if href.startswith("http"):
                        return href

        return ""
