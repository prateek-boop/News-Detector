import time
import requests
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """
    Get all hackathon URLs from Devpost using their API.
    
    This uses Devpost's internal API to fetch all hackathons efficiently
    without browser automation. Much faster and more reliable.
    
    USAGE:
    
      # Get all hackathon URLs
      python manage.py get_devpost_urls_api
      
      # Save to file
      python manage.py get_devpost_urls_api --output devpost_urls.txt
      
      # Get specific status
      python manage.py get_devpost_urls_api --status open
    
    EXAMPLES:
    
      # Get all URLs and save
      python manage.py get_devpost_urls_api --output devpost_all.txt
      
      # Get only open hackathons
      python manage.py get_devpost_urls_api --status open --output devpost_open.txt
      
      # Show statistics
      python manage.py get_devpost_urls_api --show-stats
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
            help='Output file to save URLs',
        )
        parser.add_argument(
            '--show-stats',
            action='store_true',
            help='Show statistics',
        )

    def fetch_page(self, page, status='all'):
        """Fetch a single page of hackathons"""
        # Devpost API endpoint (reverse engineered from network tab)
        url = "https://devpost.com/api/hackathons"
        
        params = {
            'page': page,
            'per_page': 25,  # Devpost loads 25 at a time
            'challenge_type[]': 'all',
        }
        
        if status != 'all':
            params['status[]'] = status
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching page {page}: {str(e)}"))
            return None

    def handle(self, *args, **options):
        status = options['status']
        output_file = options.get('output')
        show_stats = options['show_stats']
        
        self.stdout.write(self.style.SUCCESS("Starting Devpost URL fetcher (API mode)..."))
        self.stdout.write("This will fetch ALL hackathon URLs from Devpost API")
        
        all_urls = set()
        page = 1
        total_pages = None
        empty_count = 0
        
        while True:
            self.stdout.write(f"Fetching page {page}... (Total URLs: {len(all_urls)})")
            
            data = self.fetch_page(page, status)
            
            if not data:
                empty_count += 1
                if empty_count >= 3:
                    self.stdout.write("Multiple empty responses, stopping")
                    break
                page += 1
                continue
            
            # Reset empty counter on successful fetch
            empty_count = 0
            
            # Extract hackathons from response
            hackathons = data.get('hackathons', [])
            
            if not hackathons:
                self.stdout.write("No more hackathons found")
                break
            
            # Extract URLs
            urls_this_page = 0
            for hack in hackathons:
                url = hack.get('url')
                if url and '.devpost.com' in url:
                    # Normalize URL
                    base_url = url.split('?')[0].split('#')[0].rstrip('/')
                    if base_url not in all_urls:
                        all_urls.add(base_url)
                        urls_this_page += 1
            
            # Show progress every page
            self.stdout.write(f"  Page {page}: +{urls_this_page} new URLs (Total: {len(all_urls)})")
            
            # Check if there are more pages
            meta = data.get('meta', {})
            total_count = meta.get('total_count', 0)
            
            if total_count and not total_pages:
                total_pages = (total_count + 24) // 25
                self.stdout.write(f"Expected {total_count} total hackathons (~{total_pages} pages)")
            
            # If we got fewer results than expected, we're done
            if len(hackathons) < 25:
                self.stdout.write(f"Got {len(hackathons)} hackathons (less than 25), end of results")
                break
            
            page += 1
            time.sleep(0.3)  # Be polite to the server
            
            # Safety limit - continue until we reach all pages
            if page > 2000:
                self.stdout.write("Reached safety limit (page 2000)")
                break
        
        # Final results
        urls = sorted(all_urls)
        self.stdout.write(self.style.SUCCESS(f"\n✓ Found {len(urls)} unique hackathon URLs"))
        
        if show_stats:
            self.stdout.write(f"\nStatistics:")
            self.stdout.write(f"  Total URLs: {len(urls)}")
            self.stdout.write(f"  Pages fetched: {page}")
        
        # Save to file
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
