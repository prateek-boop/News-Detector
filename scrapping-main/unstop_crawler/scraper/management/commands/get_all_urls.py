import requests
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """
    Get all unique URLs of hackathons and/or competitions from Unstop.
    
    Fetches every single opportunity URL without duplicates.
    
    Examples:
      python manage.py get_all_urls --type hackathons
      python manage.py get_all_urls --type competitions
      python manage.py get_all_urls --type both
      python manage.py get_all_urls --type hackathons --output urls.txt
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['hackathons', 'competitions', 'both'],
            default='hackathons',
            help='Type of opportunities to fetch (default: hackathons)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file to save URLs (optional)',
        )
        parser.add_argument(
            '--show-stats',
            action='store_true',
            help='Show statistics about the URLs',
        )

    def handle(self, *args, **options):
        opportunity_type = options['type']
        output_file = options['output']
        show_stats = options['show_stats']
        
        all_urls = set()  # Use set to avoid duplicates
        
        types_to_fetch = []
        if opportunity_type == 'both':
            types_to_fetch = ['hackathons', 'competitions']
        else:
            types_to_fetch = [opportunity_type]
        
        for opp_type in types_to_fetch:
            self.stdout.write(f"\nFetching all {opp_type} from Unstop...")
            urls = self.fetch_all_urls(opp_type)
            all_urls.update(urls)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Found {len(urls)} {opp_type}")
            )
        
        # Convert to sorted list
        all_urls = sorted(list(all_urls))
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS(
            f"Total unique URLs: {len(all_urls)}"
        ))
        self.stdout.write("="*70)
        
        # Show statistics if requested
        if show_stats:
            self.show_statistics(all_urls)
        
        # Save to file if requested
        if output_file:
            self.save_to_file(all_urls, output_file)
        else:
            # Print to stdout
            self.stdout.write("\nURLs:\n")
            for url in all_urls:
                self.stdout.write(url)
    
    def fetch_all_urls(self, opportunity_type):
        """Fetch all URLs for a given opportunity type"""
        urls = set()
        page = 1
        per_page = 100  # Maximum per page
        
        while True:
            api_url = f"https://unstop.com/api/public/opportunity/search-result?opportunity={opportunity_type}&page={page}&per_page={per_page}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "Accept": "application/json",
            }
            
            try:
                response = requests.get(api_url, headers=headers, timeout=30)
                
                if response.status_code != 200:
                    self.stdout.write(
                        self.style.ERROR(f"Error: API returned {response.status_code}")
                    )
                    break
                
                data = response.json()
                
                if "data" not in data or "data" not in data["data"]:
                    break
                
                opportunities = data["data"]["data"]
                
                if not opportunities:
                    break
                
                # Extract URLs
                for opp in opportunities:
                    public_url = opp.get("public_url", "")
                    if public_url:
                        if not public_url.startswith("http"):
                            full_url = f"https://unstop.com/{public_url}"
                        else:
                            full_url = public_url
                        urls.add(full_url)
                
                # Progress indicator
                self.stdout.write(
                    f"  Page {page}: {len(opportunities)} items (Total: {len(urls)})",
                    ending='\r'
                )
                
                # Check if we've reached the end
                total = data["data"]["total"]
                if page * per_page >= total:
                    break
                
                page += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"\nError on page {page}: {str(e)}")
                )
                break
        
        self.stdout.write("")  # New line after progress
        return urls
    
    def show_statistics(self, urls):
        """Show statistics about the URLs"""
        self.stdout.write("\n" + "="*70)
        self.stdout.write("STATISTICS:")
        self.stdout.write("="*70)
        
        hackathon_count = sum(1 for url in urls if '/hackathons/' in url)
        competition_count = sum(1 for url in urls if '/competitions/' in url)
        other_count = len(urls) - hackathon_count - competition_count
        
        self.stdout.write(f"  Hackathons:   {hackathon_count}")
        self.stdout.write(f"  Competitions: {competition_count}")
        if other_count > 0:
            self.stdout.write(f"  Other:        {other_count}")
        
        # Organizer stats (from URL patterns)
        organizers = {}
        for url in urls:
            # Extract organizer slug from URL (last part before ID)
            parts = url.rstrip('/').split('-')
            if len(parts) >= 2 and parts[-1].isdigit():
                # Get organization name (everything before the final ID)
                org_parts = parts[:-1]
                if '/hackathons/' in url:
                    org_parts = org_parts[1:]  # Remove 'hackathons' part
                elif '/competitions/' in url:
                    org_parts = org_parts[1:]  # Remove 'competitions' part
                
                org_name = ' '.join(org_parts[-5:])  # Last 5 words as org name
                organizers[org_name] = organizers.get(org_name, 0) + 1
        
        if organizers:
            top_orgs = sorted(organizers.items(), key=lambda x: x[1], reverse=True)[:10]
            self.stdout.write(f"\nTop 10 Organizers:")
            for org, count in top_orgs:
                self.stdout.write(f"  {count:4d}x {org[:50]}")
    
    def save_to_file(self, urls, filename):
        """Save URLs to a file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for url in urls:
                    f.write(url + '\n')
            
            self.stdout.write("\n" + "="*70)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Saved {len(urls)} URLs to: {filename}")
            )
            self.stdout.write("="*70)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error saving to file: {str(e)}")
            )
