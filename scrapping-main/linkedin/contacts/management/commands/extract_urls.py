from django.core.management.base import BaseCommand
from seleniumbase import SB
import os
import json
import csv
import time

class Command(BaseCommand):
    help = 'Extract LinkedIn profile URLs from post comments (fast, no detailed scraping)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            required=True,
            help='LinkedIn post URL to extract profiles from'
        )
        parser.add_argument(
            '--visible',
            action='store_true',
            help='Run browser in visible mode instead of headless'
        )
        parser.add_argument(
            '--fast',
            action='store_true',
            help='Skip comment loading, only get visible profiles'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='profile_urls',
            help='Output filename without extension (default: profile_urls)'
        )

    def handle(self, *args, **options):
        url = options['url']
        headless = not options['visible']
        fast_mode = options['fast']
        output_name = options['output']
        profile_dir = os.path.abspath("./profile")
        
        start_time = time.time()
        
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("LinkedIn Profile URL Extractor"))
        self.stdout.write(f"Target: {url}")
        self.stdout.write(f"Mode: {'HEADLESS' if headless else 'VISIBLE'}")
        if fast_mode:
            self.stdout.write("Fast mode: ON (no comment loading)")
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
                
                # Progressive loading and extraction
                if not fast_mode:
                    self.stdout.write("Starting progressive scraping...")
                    clicks = 0
                    no_button_count = 0
                    max_clicks = 20 if limit and limit <= 50 else 100
                    all_urls = set()
                    
                    while clicks < max_clicks:
                        try:
                            # Extract URLs from current page state
                            current_urls = sb.execute_script(r"""
                                const urls = new Set();
                                document.querySelectorAll('a[href*="/in/"]').forEach(link => {
                                    const href = link.href;
                                    if (href.includes('/in/') && !href.includes('/company/')) {
                                        const cleanUrl = href.split('?')[0].split('#')[0];
                                        if (cleanUrl.match(/linkedin\.com\/in\/[^\/]+\/?$/)) {
                                            urls.add(cleanUrl);
                                        }
                                    }
                                });
                                return Array.from(urls);
                            """)
                            
                            # Add new URLs to set
                            new_urls = set(current_urls) - all_urls
                            if new_urls:
                                all_urls.update(new_urls)
                                self.stdout.write(f"  Found {len(new_urls)} new URLs (Total: {len(all_urls)})")
                            
                            # Try to load more comments
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
                                    no_button_count = 0
                                    
                                    if clicks % 10 == 0:
                                        self.stdout.write(f"  Comment loads: {clicks}")
                                    
                                    sb.sleep(0.8)
                                    break
                            
                            if not button_found:
                                no_button_count += 1
                                if no_button_count > 3:
                                    break
                                sb.sleep(1)
                                
                        except Exception as e:
                            no_button_count += 1
                            if no_button_count > 3:
                                break
                            sb.sleep(1)
                    
                    # Final extraction
                    profile_urls = sb.execute_script(r"""
                        const urls = new Set();
                        document.querySelectorAll('a[href*="/in/"]').forEach(link => {
                            const href = link.href;
                            if (href.includes('/in/') && !href.includes('/company/')) {
                                const cleanUrl = href.split('?')[0].split('#')[0];
                                if (cleanUrl.match(/linkedin\.com\/in\/[^\/]+\/?$/)) {
                                    urls.add(cleanUrl);
                                }
                            }
                        });
                        return Array.from(urls);
                    """)
                    
                    self.stdout.write(f"\nProgressive scraping complete!")
                    self.stdout.write(f"Total clicks: {clicks}")
                    self.stdout.write(f"Total URLs found: {len(profile_urls)}\n")
                else:
                    self.stdout.write("Fast mode: Skipping comment loading\n")
                    profile_urls = sb.execute_script(r"""
                        const urls = new Set();
                        document.querySelectorAll('a[href*="/in/"]').forEach(link => {
                            const href = link.href;
                            if (href.includes('/in/') && !href.includes('/company/')) {
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
                
                self.stdout.write(f"Found {len(profile_urls)} unique profile URLs\n")
                
                # Export to files
                self._export_urls(profile_urls, output_name)
                
                # Show summary
                elapsed = time.time() - start_time
                self.stdout.write("\n" + "="*70)
                self.stdout.write(self.style.SUCCESS("EXTRACTION COMPLETE"))
                self.stdout.write("="*70)
                self.stdout.write(f"Total URLs extracted:  {len(profile_urls)}")
                self.stdout.write(f"Time taken:            {elapsed:.1f}s")
                self.stdout.write(f"Output files:")
                self.stdout.write(f"  - {output_name}.txt")
                self.stdout.write(f"  - {output_name}.json")
                self.stdout.write(f"  - {output_name}.csv")
                self.stdout.write("="*70)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\nFatal error: {str(e)}"))
    
    def _export_urls(self, urls, output_name):
        """Export URLs to TXT, JSON, and CSV"""
        import time
        
        # Export to TXT (one per line)
        txt_file = f"{output_name}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(url + '\n')
        
        # Export to JSON
        json_file = f"{output_name}.json"
        data = [{'index': idx, 'profile_url': url} for idx, url in enumerate(urls, 1)]
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Export to CSV
        csv_file = f"{output_name}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['index', 'profile_url'])
            for idx, url in enumerate(urls, 1):
                writer.writerow([idx, url])
        
        self.stdout.write(f"\nExported {len(urls)} URLs to:")
        self.stdout.write(f"  - {txt_file}")
        self.stdout.write(f"  - {json_file}")
        self.stdout.write(f"  - {csv_file}")
