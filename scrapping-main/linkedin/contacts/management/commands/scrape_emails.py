from django.core.management.base import BaseCommand
from seleniumbase import SB
from contacts.models import Contact
import time
import re
import json
import csv
import os

class Command(BaseCommand):
    help = 'Scrape ALL emails from LinkedIn posts - COMPLETE VERSION'

    def add_arguments(self, parser):
        parser.add_argument('--url', type=str, required=True, help='LinkedIn post URL')
        parser.add_argument('--visible', action='store_true', help='Show browser')
        parser.add_argument(
            '--speed',
            type=str,
            choices=['normal', 'fast', 'aggressive'],
            default='fast',
            help='Speed mode: normal (0.8s delays), fast (0.3s delays), aggressive (0.15s delays). Default: fast'
        )
        parser.add_argument(
            '--profile-dir',
            type=str,
            default='./profile2',
            help='Chrome profile directory (default: ./profile2)'
        )

    def handle(self, *args, **options):
        url = options['url']
        headless = not options['visible']
        speed_mode = options['speed']
        profile_dir = os.path.abspath(options['profile_dir'])
        
        # Set delays based on speed mode
        if speed_mode == 'normal':
            scroll_delay = 0.8
            button_delay = 2.0
            initial_delay = 1.0
        elif speed_mode == 'fast':
            scroll_delay = 0.3
            button_delay = 0.8
            initial_delay = 0.5
        else:  # aggressive
            scroll_delay = 0.15
            button_delay = 0.4
            initial_delay = 0.3
        
        start_time = time.time()
        
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("LinkedIn Email Scraper - ULTIMATE MODE"))
        self.stdout.write(f"Target: {url}")
        self.stdout.write(f"Mode: {'HEADLESS' if headless else 'VISIBLE'}")
        self.stdout.write(f"Speed: {speed_mode.upper()} (scroll: {scroll_delay}s, button: {button_delay}s)")
        self.stdout.write(f"Profile: {profile_dir}")
        self.stdout.write("="*70 + "\n")
        
        try:
            with SB(uc=True, headless=headless, user_data_dir=profile_dir) as sb:
                
                # STEP 1: Open page
                self.stdout.write("➤ Opening LinkedIn post...")
                sb.open(url)
                sb.sleep(3)  # Page load wait
                
                # Check login
                if 'authwall' in sb.get_current_url() or 'login' in sb.get_current_url():
                    self.stdout.write(self.style.ERROR("  Not logged in!"))
                    return
                
                # STEP 2: Click to open comments section
                self.stdout.write("➤ Opening comments section...")
                sb.execute_script("""
                    document.querySelectorAll('button, span').forEach(el => {
                        const text = el.textContent.toLowerCase();
                        if (text.includes('comment') && !text.includes('add')) {
                            try { el.click(); } catch(e) {}
                        }
                    });
                """)
                sb.sleep(button_delay)
                
                # STEP 3: CRITICAL - Change dropdown to "Most Recent"
                self.stdout.write("➤ Changing sort to 'Most Recent'...")
                changed = False
                
                # Try multiple methods to find and click the dropdown
                try:
                    # Method 1: Find by aria-label
                    dropdowns = sb.find_elements('button[aria-label*="sort" i], button[aria-label*="relevant" i]')
                    for dropdown in dropdowns:
                        try:
                            sb.click(dropdown)
                            sb.sleep(initial_delay)
                            changed = True
                            self.stdout.write("  Dropdown opened")
                            break
                        except:
                            pass
                except:
                    pass
                
                # Method 2: JavaScript click
                if not changed:
                    try:
                        sb.execute_script("""
                            document.querySelectorAll('button').forEach(btn => {
                                const text = btn.textContent.toLowerCase();
                                const aria = (btn.getAttribute('aria-label') || '').toLowerCase();
                                if (text.includes('relevant') || aria.includes('sort') || text.includes('most')) {
                                    btn.click();
                                }
                            });
                        """)
                        sb.sleep(button_delay)
                        changed = True
                        self.stdout.write("  Dropdown opened via JS")
                    except:
                        pass
                
                # Now click "Most Recent" option
                if changed:
                    try:
                        sb.execute_script("""
                            document.querySelectorAll('div, li, span, button').forEach(el => {
                                const text = el.textContent.toLowerCase();
                                if (text.includes('most recent') || text.includes('recent')) {
                                    try { el.click(); } catch(e) {}
                                }
                            });
                        """)
                        sb.sleep(button_delay)
                        self.stdout.write(self.style.SUCCESS("  Changed to 'Most Recent'"))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Could not select 'Most Recent': {e}"))
                
                # STEP 4: Initial scroll to load comments
                self.stdout.write("➤ Initial loading...")
                for _ in range(10):
                    sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    sb.sleep(initial_delay)
                
                # Count initial comments
                initial_count = sb.execute_script("""
                    return document.querySelectorAll('.comments-comment-item, article[data-urn*="comment"], [class*="comment-item"]').length;
                """)
                self.stdout.write(f"➤ Initial comments: {initial_count}")
                
                # STEP 5: INFINITE SCROLL - Load ALL comments
                self.stdout.write("\n➤ INFINITE SCROLL - Loading ALL comments...\n")
                
                total_scrolls = 0
                total_clicks = 0
                no_change_count = 0
                previous_comment_count = 0
                max_no_change = 5  # Very patient
                
                while no_change_count < max_no_change:
                    # Scroll everything
                    sb.execute_script("""
                        window.scrollTo(0, document.body.scrollHeight);
                        document.querySelectorAll('*').forEach(el => {
                            if (el.scrollHeight > el.clientHeight) {
                                el.scrollTop = el.scrollHeight;
                            }
                        });
                    """)
                    sb.sleep(scroll_delay)
                    total_scrolls += 1
                    
                    # Click ALL load more buttons
                    if total_scrolls % 2 == 0:
                        clicks = sb.execute_script("""
                            var count = 0;
                            document.querySelectorAll('button, span[role="button"], div[role="button"]').forEach(function(btn) {
                                if (!btn.offsetParent) return;
                                var text = (btn.textContent || '').toLowerCase();
                                var aria = (btn.getAttribute('aria-label') || '').toLowerCase();
                                var combined = text + ' ' + aria;
                                
                                if ((combined.includes('load') || combined.includes('more') || 
                                     combined.includes('show') || combined.includes('previous')) && 
                                    combined.includes('comment')) {
                                    try {
                                        btn.click();
                                        count++;
                                    } catch(e) {}
                                }
                            });
                            return count;
                        """)
                        
                        if clicks and clicks > 0:
                            total_clicks += clicks
                            if total_scrolls % 10 == 0:
                                self.stdout.write(f"  Scroll {total_scrolls:3d} | Clicked {clicks} buttons | Total clicks: {total_clicks}")
                            sb.sleep(button_delay)
                    
                    # Count comments
                    current_comment_count = sb.execute_script("""
                        return document.querySelectorAll('.comments-comment-item, article[data-urn*="comment"], [class*="comment-item"]').length;
                    """)
                    
                    # Extract and save every 10 scrolls
                    if total_scrolls % 10 == 0:
                        page_source = sb.get_page_source()
                        new_emails = self._extract_and_save_emails(page_source)
                        total_db = Contact.objects.count()
                        
                        if current_comment_count > previous_comment_count or new_emails > 0:
                            no_change_count = 0
                            previous_comment_count = current_comment_count
                            self.stdout.write(f"  Scroll {total_scrolls:3d} | Comments: {current_comment_count:4d} | DB: {total_db:4d} emails | +{new_emails} new")
                        else:
                            no_change_count += 1
                            if total_scrolls % 20 == 0:
                                self.stdout.write(f"  Scroll {total_scrolls:3d} | No change ({no_change_count}/{max_no_change})")
                    
                    # Vary scrolling
                    if total_scrolls % 20 == 0:
                        sb.execute_script("window.scrollTo(0, 0);")
                        sb.sleep(scroll_delay)
                
                self.stdout.write(f"\nInfinite scroll complete: {total_scrolls} scrolls, {total_clicks} button clicks")
                self.stdout.write(f"Total comments loaded: {current_comment_count}")
                
                # STEP 6: Final mega extraction
                self.stdout.write("\n➤ Final deep extraction...")
                for i in range(30):
                    sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    sb.sleep(scroll_delay)
                    
                    if i % 5 == 0:
                        page_source = sb.get_page_source()
                        new = self._extract_and_save_emails(page_source)
                        if new > 0:
                            self.stdout.write(f"  💾 Final pass {i}/30 | +{new} new emails")
                
                # STEP 7: Extract all emails from full page
                self.stdout.write("➤ Final complete extraction...")
                page_source = sb.get_page_source()
                
                email_pattern = r'\b[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}\b'
                all_emails = re.findall(email_pattern, page_source)
                
                valid_emails = []
                for email in all_emails:
                    lower = email.lower()
                    if any(ext in lower for ext in ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp']):
                        continue
                    if any(domain in lower for domain in ['linkedin.com', 'sentry.io', 'gravatar.com']):
                        continue
                    if re.search(r'\.(com|in|org|net|edu|gov|co|io|ai|tech|dev|ac|uk)$', lower):
                        valid_emails.append(lower)
                
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
                        if new_count <= 10:  # Show first 10 new
                            self.stdout.write(self.style.SUCCESS(f"  + NEW: {email}"))
                    else:
                        if not contact.name:
                            contact.name = name
                            contact.save()
                        exists_count += 1
                
                # Save to files
                txt_file = 'linkedin_emails.txt'
                json_file = 'linkedin_emails.json'
                csv_file = 'linkedin_emails.csv'
                
                with open(txt_file, 'w') as f:
                    f.write('\n'.join(unique_emails))
                
                with open(json_file, 'w') as f:
                    json.dump([{"index": i, "email": e} for i, e in enumerate(unique_emails, 1)], f, indent=2)
                
                with open(csv_file, 'w', newline='') as f:
                    if unique_emails:
                        writer = csv.DictWriter(f, fieldnames=['index', 'email'])
                        writer.writeheader()
                        writer.writerows([{"index": i, "email": e} for i, e in enumerate(unique_emails, 1)])
                
                elapsed = time.time() - start_time
                
                # Final summary
                self.stdout.write("\n" + "="*70)
                self.stdout.write(self.style.SUCCESS("🎉 SCRAPING COMPLETE"))
                self.stdout.write("="*70)
                self.stdout.write(f"  ✓ New emails added:     {new_count}")
                self.stdout.write(f"  ✓ Already in database:  {exists_count}")
                self.stdout.write(f"  ✓ Total in database:    {Contact.objects.count()}")
                self.stdout.write(f"  ✓ Files: {txt_file}, {json_file}, {csv_file}")
                self.stdout.write(f"  ✓ Time: {elapsed:.1f}s")
                self.stdout.write(f"  ✓ Comments loaded: {current_comment_count}")
                self.stdout.write(f"  ✓ Button clicks: {total_clicks}")
                self.stdout.write("="*70 + "\n")
                
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\n⚠ Interrupted by user"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {str(e)}"))
            import traceback
            traceback.print_exc()
    
    def _extract_and_save_emails(self, page_source):
        """Extract and save emails progressively"""
        email_pattern = r'\b[A-Za-z0-9][A-Za-z0-9._%+-]*@[A-Za-z0-9][A-Za-z0-9.-]*\.[A-Za-z]{2,}\b'
        all_emails = re.findall(email_pattern, page_source)
        
        valid_emails = []
        for email in all_emails:
            lower = email.lower()
            if any(ext in lower for ext in ['.png', '.jpg', '.jpeg', '.svg', '.gif', '.webp']):
                continue
            if any(domain in lower for domain in ['linkedin.com', 'sentry.io', 'gravatar.com']):
                continue
            if re.search(r'\.(com|in|org|net|edu|gov|co|io|ai|tech|dev|ac|uk)$', lower):
                valid_emails.append(lower)
        
        new_count = 0
        for email in set(valid_emails):
            name = email.split('@')[0]
            contact, created = Contact.objects.get_or_create(email=email, defaults={'name': name})
            if created:
                new_count += 1
        
        return new_count
