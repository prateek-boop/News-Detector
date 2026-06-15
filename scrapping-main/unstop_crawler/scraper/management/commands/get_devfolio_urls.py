import requests
import time
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """
    Get all Devfolio hackathon URLs (no duplicates).
    
    Fetches URLs from open, upcoming, and past hackathons using Devfolio's API.
    Outputs unique URLs to a file.
    
    USAGE:
    
      # Get all URLs and save to file
      python manage.py get_devfolio_urls
      
      # Save to custom file
      python manage.py get_devfolio_urls --output custom_urls.txt
      
      # Get only specific status
      python manage.py get_devfolio_urls --status open
      python manage.py get_devfolio_urls --status past
      python manage.py get_devfolio_urls --status upcoming
      
      # Get all statuses (default)
      python manage.py get_devfolio_urls --status all
    
    OPTIONS:
      --output FILE        Output file path (default: devfolio_urls.txt)
      --status STATUS      Fetch 'open', 'past', 'upcoming', or 'all' (default: all)
    
    OUTPUT:
      Creates a text file with one URL per line, no duplicates
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="devfolio_urls.txt",
            help="Output file path (default: devfolio_urls.txt)",
        )
        parser.add_argument(
            "--status",
            type=str,
            choices=['open', 'past', 'upcoming', 'all'],
            default='all',
            help="Status of hackathons to fetch (default: all)",
        )

    def handle(self, *args, **options):
        output_file = options["output"]
        status = options["status"]

        self.stdout.write(self.style.SUCCESS("Fetching Devfolio hackathon URLs..."))
        
        # Determine which statuses to fetch
        if status == 'all':
            statuses = ['open', 'upcoming', 'past']
        else:
            statuses = [status]

        all_urls = set()  # Use set to avoid duplicates
        
        for current_status in statuses:
            self.stdout.write(f"\nFetching {current_status.upper()} hackathons...")
            urls = self.fetch_urls_for_status(current_status)
            all_urls.update(urls)
            self.stdout.write(f"  Found {len(urls)} URLs")

        # Sort URLs for consistent output
        sorted_urls = sorted(all_urls)
        
        # Write to file
        with open(output_file, 'w') as f:
            for url in sorted_urls:
                f.write(url + '\n')
        
        self.stdout.write(self.style.SUCCESS(f"\n✓ Saved {len(sorted_urls)} unique URLs to {output_file}"))

    def fetch_urls_for_status(self, status):
        """Fetch all hackathon URLs for a given status"""
        status_map = {
            'open': 'application_open',
            'upcoming': 'upcoming',
            'past': 'past'
        }
        
        api_type = status_map.get(status, 'application_open')
        api_url = "https://api.devfolio.co/api/search/hackathons"
        
        urls = []
        page_size = 100
        from_index = 0
        
        while True:
            payload = {
                "type": api_type,
                "from": from_index,
                "size": page_size
            }
            
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            }
            
            try:
                response = requests.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                hits = data.get('hits', {}).get('hits', [])
                total = data.get('hits', {}).get('total', {}).get('value', 0)
                
                if not hits:
                    break
                
                # Extract URLs from hits
                for hit in hits:
                    source = hit.get('_source', {})
                    slug = source.get('slug')
                    if slug:
                        url = f"https://{slug}.devfolio.co/overview"
                        urls.append(url)
                
                self.stdout.write(f"  Fetched {len(urls)}/{total}...", ending='\r')
                
                if len(urls) >= total:
                    break
                    
                from_index += page_size
                time.sleep(0.5)  # Be respectful to API
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n  API error: {str(e)}"))
                break
        
        return urls
