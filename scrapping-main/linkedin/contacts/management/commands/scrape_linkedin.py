from django.core.management.base import BaseCommand
from seleniumbase import SB
import re
from contacts.models import Contact

class Command(BaseCommand):
    help = 'Scrape emails from LinkedIn post comments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            required=True,
            help='LinkedIn post URL to scrape (required)'
        )

    def handle(self, *args, **options):
        url = options['url']
        profile_dir = "/home/sonu/Desktop/linkedin/profile"
        
        self.stdout.write("="*70)
        self.stdout.write("LinkedIn Email Scraper - Fast Mode")
        self.stdout.write(f"Target: {url}")
        self.stdout.write("="*70 + "\n")
        
        try:
            with SB(uc=True, headless=True, user_data_dir=profile_dir) as sb:
                
                self.stdout.write("➤ Opening LinkedIn post...")
                sb.open(url)
                sb.sleep(3)
                
                # Continuously click "Load more comments" until no more exist
                self.stdout.write("➤ Loading ALL comments (this may take time)...")
                clicks = 0
                no_button_count = 0
                
                while True:
                    try:
                        # Scroll down to load more content and find button
                        sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        sb.sleep(0.5)
                        
                        # Try multiple selectors for the "Load more" button
                        button_found = False
                        
                        # Selector 1: Class-based
                        if sb.is_element_present("button.comments-comments-list__load-more-comments-button--cr"):
                            sb.click("button.comments-comments-list__load-more-comments-button--cr")
                            button_found = True
                            
                        # Selector 2: Text-based
                        elif sb.is_element_present("button:contains('Load more comments')"):
                            sb.click("button:contains('Load more comments')")
                            button_found = True
                            
                        # Selector 3: Attribute-based
                        elif sb.is_element_present("button[aria-label*='Load more']"):
                            sb.click("button[aria-label*='Load more']")
                            button_found = True
                        
                        if button_found:
                            clicks += 1
                            no_button_count = 0
                            
                            # Save to database every 10 clicks
                            if clicks % 10 == 0:
                                page_source = sb.get_page_source()
                                emails_found = self._extract_and_save_emails(page_source)
                                self.stdout.write(f"  ✓ Clicks: {clicks} | Emails in DB: {Contact.objects.count()}")
                            
                            sb.sleep(0.8)  # Fast but safe delay
                        else:
                            no_button_count += 1
                            if no_button_count > 3:
                                break
                            sb.sleep(1)
                            
                    except Exception as e:
                        no_button_count += 1
                        if no_button_count > 3:
                            break
                        sb.sleep(1)
                
                self.stdout.write(f"\n✓ Total button clicks: {clicks}")
                
                # Final scroll to ensure all content is loaded
                self.stdout.write("➤ Final scroll pass...")
                for _ in range(10):
                    sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    sb.sleep(0.5)
                
                # Final extraction
                self.stdout.write("➤ Final extraction...")
                page_source = sb.get_page_source()
                
                # Find all emails
                email_pattern = r'\b[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}\b'
                all_emails = re.findall(email_pattern, page_source)
                
                # Filter valid emails
                valid_emails = []
                for email in all_emails:
                    lower = email.lower()
                    if any(ext in lower for ext in ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp']):
                        continue
                    if any(domain in lower for domain in ['linkedin.com', 'sentry.io', 'gravatar.com']):
                        continue
                    if re.search(r'\.(com|in|org|net|edu|gov|co|io|ai|tech|dev|ac)$', lower):
                        valid_emails.append(email)
                
                unique_emails = sorted(list(set(valid_emails)))
                
                self.stdout.write("\n" + "="*70)
                self.stdout.write(self.style.SUCCESS(f"✓ Found {len(unique_emails)} unique emails"))
                self.stdout.write("="*70 + "\n")
                
                # Save to database
                new_count = 0
                exists_count = 0
                
                for email in unique_emails:
                    name = email.split('@')[0]
                    contact, created = Contact.objects.get_or_create(
                        email=email,
                        defaults={'name': name}
                    )
                    
                    if created:
                        new_count += 1
                        self.stdout.write(self.style.SUCCESS(f"  + NEW: {name} <{email}>"))
                    else:
                        if not contact.name:
                            contact.name = name
                            contact.save()
                        exists_count += 1
                
                # Final summary
                self.stdout.write("\n" + "="*70)
                self.stdout.write(self.style.SUCCESS("SCRAPING COMPLETE"))
                self.stdout.write("="*70)
                self.stdout.write(f"  ✓ New emails added:     {new_count}")
                self.stdout.write(f"  ✓ Already in database:  {exists_count}")
                self.stdout.write(f"  ✓ Total in database:    {Contact.objects.count()}")
                self.stdout.write("="*70 + "\n")
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\n⚠ Interrupted by user"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {str(e)}"))
            import traceback
            traceback.print_exc()
    
    def _extract_and_save_emails(self, page_source):
        """Extract and save emails incrementally"""
        email_pattern = r'\b[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}\b'
        all_emails = re.findall(email_pattern, page_source)
        
        valid_emails = []
        for email in all_emails:
            lower = email.lower()
            if any(ext in lower for ext in ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp']):
                continue
            if any(domain in lower for domain in ['linkedin.com', 'sentry.io', 'gravatar.com']):
                continue
            if re.search(r'\.(com|in|org|net|edu|gov|co|io|ai|tech|dev|ac)$', lower):
                valid_emails.append(email)
        
        # Save new emails
        for email in set(valid_emails):
            name = email.split('@')[0]
            Contact.objects.get_or_create(email=email, defaults={'name': name})
        
        return len(set(valid_emails))


