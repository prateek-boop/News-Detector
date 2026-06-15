from django.core.management.base import BaseCommand
from seleniumbase import SB
from contacts.models import Contact, Profile
import time
import re
import os

class Command(BaseCommand):
    help = 'Scrape both emails and profiles from a LinkedIn post in one command'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            required=True,
            help='LinkedIn post URL to scrape'
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
        parser.add_argument(
            '--skip-emails',
            action='store_true',
            help='Skip email scraping, only scrape profiles'
        )
        parser.add_argument(
            '--skip-profiles',
            action='store_true',
            help='Skip profile scraping, only scrape emails'
        )
        parser.add_argument(
            '--fast',
            action='store_true',
            help='Skip comment loading, only scrape visible profiles (much faster for testing)'
        )
        parser.add_argument(
            '--speed',
            type=str,
            choices=['normal', 'fast', 'aggressive'],
            default='fast',
            help='Speed mode: normal (0.8s delays), fast (0.3s delays), aggressive (0.1s delays). Default: fast'
        )
        parser.add_argument(
            '--profile-dir',
            type=str,
            default='./profile',
            help='Chrome profile directory (default: ./profile)'
        )

    def handle(self, *args, **options):
        url = options['url']
        headless = not options['visible']
        limit = options['limit']
        skip_emails = options['skip_emails']
        skip_profiles = options['skip_profiles']
        fast_mode = options['fast']
        speed_mode = options['speed']
        profile_dir = os.path.abspath(options['profile_dir'])
        
        # Set delays based on speed mode
        if speed_mode == 'normal':
            scroll_delay = 0.5
            button_delay = 0.8
        elif speed_mode == 'fast':
            scroll_delay = 0.2
            button_delay = 0.3
        else:  # aggressive
            scroll_delay = 0.1
            button_delay = 0.15
        
        start_time = time.time()
        
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("LinkedIn Complete Scraper"))
        self.stdout.write(f"Target: {url}")
        self.stdout.write(f"Mode: {'HEADLESS' if headless else 'VISIBLE'}")
        self.stdout.write(f"Speed: {speed_mode.upper()} (scroll: {scroll_delay}s, button: {button_delay}s)")
        self.stdout.write(f"Profile: {profile_dir}")
        if fast_mode:
            self.stdout.write("Fast mode: ON (no comment loading)")
        if limit:
            self.stdout.write(f"Profile limit: {limit}")
        self.stdout.write("="*70 + "\n")
        
        try:
            with SB(uc=True, headless=headless, user_data_dir=profile_dir) as sb:
                
                # Open post
                self.stdout.write("Opening LinkedIn post...")
                sb.open(url)
                sb.sleep(5)
                
                if 'authwall' in sb.get_current_url() or 'login' in sb.get_current_url():
                    self.stdout.write(self.style.ERROR("  Error: Not logged in to LinkedIn"))
                    return
                
                # Switch to "Most Recent" comments
                self.stdout.write("Switching to 'Most Recent' comments...")
                try:
                    # Try to find and click the sort dropdown
                    sb.execute_script("""
                        const buttons = document.querySelectorAll('button');
                        buttons.forEach(btn => {
                            const text = btn.textContent.toLowerCase();
                            if (text.includes('relevant') || text.includes('sort')) {
                                btn.click();
                            }
                        });
                    """)
                    sb.sleep(2)
                    
                    # Click "Most Recent" option
                    sb.execute_script("""
                        const options = document.querySelectorAll('div, span, li');
                        options.forEach(opt => {
                            const text = opt.textContent.toLowerCase();
                            if (text.includes('most recent') || text.includes('recent')) {
                                opt.click();
                            }
                        });
                    """)
                    sb.sleep(2)
                    self.stdout.write("  Switched to Most Recent\n")
                except:
                    self.stdout.write("  Could not switch sorting (continuing anyway)\n")
                
                # Progressive loading and extraction (skip if fast mode)
                if not fast_mode:
                    self.stdout.write("Starting progressive scraping...\n")
                    clicks = 0
                    max_clicks = 20 if limit and limit <= 50 else 100
                    all_profile_urls = set()
                    all_emails = set()
                    
                    while clicks < max_clicks:
                        try:
                            # Extract profile URLs from current page
                            current_urls = sb.execute_script(r"""
                                (function() {
                                    const profileUrls = new Set();
                                    document.querySelectorAll('a[href*="/in/"]').forEach(link => {
                                        const href = link.href;
                                        if (href.includes('/in/') && !href.includes('/company/')) {
                                            const cleanUrl = href.split('?')[0].split('#')[0];
                                            if (cleanUrl.match(/linkedin\.com\/in\/[^\/]+\/?$/)) {
                                                profileUrls.add(cleanUrl);
                                            }
                                        }
                                    });
                                    return Array.from(profileUrls);
                                })();
                            """)
                            
                            # Save new profile URLs immediately
                            new_urls = set(current_urls) - all_profile_urls
                            if new_urls and not skip_profiles:
                                for url in new_urls:
                                    if not Profile.objects.filter(linkedin_url=url).exists():
                                        Profile.objects.create(linkedin_url=url, contact=None)
                                all_profile_urls.update(new_urls)
                                self.stdout.write(f"  Profiles: +{len(new_urls)} new (Total: {len(all_profile_urls)})")
                            
                            # Extract emails from current page
                            if not skip_emails:
                                page_source = sb.get_page_source()
                                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                                current_emails = set(re.findall(email_pattern, page_source))
                                
                                spam_domains = ['example.com', 'test.com', 'linkedin.com']
                                valid_emails = [
                                    email for email in current_emails 
                                    if not any(domain in email.lower() for domain in spam_domains)
                                ]
                                
                                new_emails = set(valid_emails) - all_emails
                                if new_emails:
                                    for email in new_emails:
                                        name = email.split('@')[0]
                                        Contact.objects.get_or_create(
                                            email=email,
                                            defaults={'name': name}
                                        )
                                    all_emails.update(new_emails)
                                    self.stdout.write(f"  Emails: +{len(new_emails)} new (Total: {len(all_emails)})")
                            
                            # Try to load more comments
                            sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                            sb.sleep(scroll_delay)
                            
                            button_found = False
                            selectors = [
                                "button.comments-comments-list__load-more-comments-button",
                                "button:contains('Load more comments')",
                                "button[aria-label*='Load more']"
                            ]
                            
                            for selector in selectors:
                                try:
                                    if sb.is_element_present(selector):
                                        sb.click(selector)
                                        button_found = True
                                        clicks += 1
                                        
                                        if clicks % 5 == 0:
                                            self.stdout.write(f"  Comment loads: {clicks}")
                                        
                                        sb.sleep(button_delay)
                                        break
                                except Exception as btn_error:
                                    # Ignore button click errors and try next selector
                                    continue
                            
                            if not button_found:
                                # Try JavaScript click as fallback (much faster)
                                try:
                                    js_click_result = sb.execute_script("""
                                        const buttons = document.querySelectorAll('button');
                                        for (let btn of buttons) {
                                            const text = btn.innerText.toLowerCase();
                                            if (text.includes('load more') || text.includes('show more')) {
                                                btn.click();
                                                return true;
                                            }
                                        }
                                        return false;
                                    """)
                                    if js_click_result:
                                        button_found = True
                                        clicks += 1
                                        if clicks % 5 == 0:
                                            self.stdout.write(f"  Comment loads: {clicks} (JS)")
                                        sb.sleep(button_delay)
                                except:
                                    pass
                                
                                if not button_found:
                                    # No button found, try a few more times before giving up
                                    if clicks > 0:  # Only break if we've already loaded some comments
                                        break
                                
                        except KeyboardInterrupt:
                            self.stdout.write("\n\nInterrupted by user. Saving progress...")
                            break
                        except Exception as e:
                            # Log error but continue
                            if "SyntaxError" not in str(e):
                                self.stdout.write(f"\n  Warning: {str(e)}")
                            # Continue even after errors
                            continue
                    
                    self.stdout.write(f"\n\nProgressive scraping complete!")
                    self.stdout.write(f"Total clicks: {clicks}")
                    
                    emails_saved = Contact.objects.count()
                    profiles_scraped = len(all_profile_urls)
                else:
                    self.stdout.write("Fast mode: Skipping comment loading\n")
                    
                    # Just get visible content
                    if not skip_profiles:
                        profile_urls = sb.execute_script(r"""
                            (function() {
                                const visibleUrls = new Set();
                                document.querySelectorAll('a[href*="/in/"]').forEach(link => {
                                    const href = link.href;
                                    if (href.includes('/in/') && !href.includes('/company/')) {
                                        const cleanUrl = href.split('?')[0].split('#')[0];
                                        if (cleanUrl.match(/linkedin\.com\/in\/[^\/]+\/?$/)) {
                                            visibleUrls.add(cleanUrl);
                                        }
                                    }
                                });
                                return Array.from(visibleUrls);
                            })();
                        """)
                        
                        for url in profile_urls:
                            if not Profile.objects.filter(linkedin_url=url).exists():
                                Profile.objects.create(linkedin_url=url, contact=None)
                        
                        profiles_scraped = len(profile_urls)
                    else:
                        profiles_scraped = 0
                    
                    if not skip_emails:
                        page_source = sb.get_page_source()
                        self._extract_and_save_emails(page_source)
                        emails_saved = Contact.objects.count()
                    else:
                        emails_saved = 0
                
                # Final summary
                elapsed = time.time() - start_time
                self.stdout.write("\n" + "="*70)
                self.stdout.write(self.style.SUCCESS("COMPLETE SCRAPING SUMMARY"))
                self.stdout.write("="*70)
                
                if not skip_emails:
                    self.stdout.write(f"Emails in database:    {emails_saved}")
                
                if not skip_profiles:
                    self.stdout.write(f"Profiles in database:  {profiles_scraped}")
                
                self.stdout.write(f"Total time:            {elapsed:.1f}s")
                self.stdout.write("="*70)
                
                # Auto export
                self.stdout.write("\nExporting data...")
                if not skip_emails:
                    self._auto_export_contacts()
                if not skip_profiles:
                    self._auto_export_profiles()
                
                self.stdout.write(self.style.SUCCESS("\nAll data saved and exported successfully!"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nFatal error: {str(e)}"))
    
    def _extract_and_save_emails(self, page_source):
        """Extract and save emails from page source"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails_found = set(re.findall(email_pattern, page_source))
        
        spam_domains = ['example.com', 'test.com', 'linkedin.com']
        valid_emails = [
            email for email in emails_found 
            if not any(domain in email.lower() for domain in spam_domains)
        ]
        
        saved_count = 0
        for email in valid_emails:
            name = email.split('@')[0]
            contact, created = Contact.objects.get_or_create(
                email=email,
                defaults={'name': name}
            )
        
        return saved_count
    
    def _auto_export_contacts(self):
        """Auto export contacts to JSON and CSV"""
        import json
        import csv
        
        contacts = Contact.objects.all()
        
        # Export JSON
        data = [{'email': c.email, 'name': c.name} for c in contacts]
        with open('contacts_export.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Export CSV
        with open('contacts_export.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['email', 'name'])
            writer.writeheader()
            for c in contacts:
                writer.writerow({'email': c.email, 'name': c.name or ''})
        
        self.stdout.write("  Contacts exported to contacts_export.json and contacts_export.csv")
    
    def _auto_export_profiles(self):
        """Auto export profiles to JSON and CSV"""
        import json
        import csv
        
        profiles = Profile.objects.select_related('contact').all()
        
        # Export JSON
        data = []
        for p in profiles:
            profile_dict = {
                'linkedin_url': p.linkedin_url,
                'contact_email': p.contact.email if p.contact else None,
            }
            data.append(profile_dict)
        
        with open('linkedin_profiles.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Export CSV
        with open('linkedin_profiles.csv', 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['linkedin_url', 'contact_email']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for p in profiles:
                writer.writerow({
                    'linkedin_url': p.linkedin_url,
                    'contact_email': p.contact.email if p.contact else '',
                })
        
        self.stdout.write("  Profiles exported to linkedin_profiles.json and linkedin_profiles.csv")
