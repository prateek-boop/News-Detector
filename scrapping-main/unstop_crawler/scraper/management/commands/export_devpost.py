import json
import csv
from django.core.management.base import BaseCommand
from scraper.models import DevpostHackathon


class Command(BaseCommand):
    help = """
    Export Devpost hackathons to JSON or CSV format.
    
    USAGE:
      python manage.py export_devpost --format json
      python manage.py export_devpost --format csv --output devpost.csv
    
    EXAMPLES:
      # Export as JSON
      python manage.py export_devpost --format json
      
      # Export as CSV with sorting
      python manage.py export_devpost --format csv --sort name
      
      # Export to specific file
      python manage.py export_devpost --output my_devpost_data.json
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv'],
            default='json',
            help='Output format (default: json)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (optional)',
        )
        parser.add_argument(
            '--sort',
            type=str,
            choices=['name', 'date', 'participants'],
            default='name',
            help='Sort order (default: name)',
        )

    def handle(self, *args, **options):
        format_type = options['format']
        output_file = options.get('output')
        sort_by = options['sort']
        
        # Get and sort hackathons
        if sort_by == 'name':
            hackathons = DevpostHackathon.objects.all().order_by('name')
        elif sort_by == 'date':
            hackathons = DevpostHackathon.objects.all().order_by('-scraped_at')
        elif sort_by == 'participants':
            # Sort numerically by converting to int, nulls last
            hackathons = list(DevpostHackathon.objects.all())
            hackathons.sort(key=lambda x: int(x.participants_count or '0'), reverse=True)
        
        if not isinstance(hackathons, list):
            hackathons = list(hackathons)
        
        total = len(hackathons)
        
        if total == 0:
            self.stdout.write(self.style.WARNING('No Devpost hackathons found in database'))
            return
        
        # Prepare data - only essential fields
        data = []
        for h in hackathons:
            data.append({
                'id': h.id,
                'name': h.name,
                'url': h.url,
                'organizer': h.organizer or '',
                'participants_count': h.participants_count or '',
                'about_content': h.about_content or '',
                'organizer_contact': h.organizer_contact or '',
                'sponsors': h.sponsors or '',
                'scraped_at': h.scraped_at.isoformat() if h.scraped_at else '',
                'updated_at': h.updated_at.isoformat() if h.updated_at else '',
            })
        
        # Export based on format
        if format_type == 'json':
            if not output_file:
                output_file = 'devpost_hackathons.json'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Exported {total} hackathons to {output_file}'))
        
        elif format_type == 'csv':
            if not output_file:
                output_file = 'devpost_hackathons.csv'
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                if data:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
            
            self.stdout.write(self.style.SUCCESS(f'✓ Exported {total} hackathons to {output_file}'))
