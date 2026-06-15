import json
import csv
from django.core.management.base import BaseCommand
from scraper.models import DevfolioHackathon


class Command(BaseCommand):
    help = """
    Export Devfolio hackathons to JSON or CSV format.
    
    This command exports all scraped Devfolio hackathon data from the database
    to structured files for analysis, backup, or integration.
    
    SUPPORTED FORMATS:
      - JSON: Structured data with all fields
      - CSV: Tabular format for spreadsheet analysis
    
    USAGE:
    
      # Export to JSON
      python manage.py export_devfolio --format json
      
      # Export to CSV
      python manage.py export_devfolio --format csv
      
      # Export with custom filename
      python manage.py export_devfolio --output my_devfolio.csv
    
    EXAMPLES:
    
      # Export as JSON sorted by name
      python manage.py export_devfolio --format json --sort name
      
      # Export only open hackathons
      python manage.py export_devfolio --status open --format csv
      
      # Export to specific file
      python manage.py export_devfolio --output exports/devfolio.json
      
      # Export sorted by date (most recent first)
      python manage.py export_devfolio --sort date
    
    SORTING OPTIONS:
      name           - Alphabetical by hackathon name
      date           - By scraped date (most recent first)
      organizer      - Alphabetical by organizer name
      participants   - By participants count (highest first)
    
    FILTER OPTIONS:
      --status open/past/upcoming - Export only specific status
    
    EXPORTED FIELDS:
      - id, name, url, organizer, status
      - participants_count, projects_count
      - about_content, start_date, end_date
      - location, mode, prizes, themes
      - organizer_contact, important_dates
      - official_website
      - scraped_at, updated_at
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
            choices=['name', 'date', 'organizer', 'participants'],
            default='date',
            help='Sort order (default: date)',
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['open', 'past', 'upcoming'],
            help='Filter by status (optional)',
        )

    def handle(self, *args, **options):
        output_format = options['format']
        output_file = options.get('output')
        sort_by = options['sort']
        status_filter = options.get('status')

        # Set default output filename if not provided
        if not output_file:
            if status_filter:
                output_file = f'devfolio_{status_filter}.{output_format}'
            else:
                output_file = f'devfolio_export.{output_format}'

        self.stdout.write(f'Exporting Devfolio hackathons to {output_file}...')

        # Get hackathons with optional filtering
        if status_filter:
            hackathons = DevfolioHackathon.objects.filter(status=status_filter)
        else:
            hackathons = DevfolioHackathon.objects.all()

        # Apply sorting
        if sort_by == 'name':
            hackathons = hackathons.order_by('name')
            sort_desc = "alphabetically by name"
        elif sort_by == 'organizer':
            hackathons = hackathons.order_by('organizer')
            sort_desc = "alphabetically by organizer"
        elif sort_by == 'participants':
            # Sort by participants count (convert to int, handle empty/null)
            hackathons_list = list(hackathons)
            hackathons_list.sort(
                key=lambda x: int(x.participants_count or '0') if (x.participants_count or '0').isdigit() else 0,
                reverse=True
            )
            hackathons = hackathons_list
            sort_desc = "by participants count (highest first)"
        else:  # date (default)
            hackathons = hackathons.order_by('-scraped_at')
            sort_desc = "by date (most recent first)"

        if not isinstance(hackathons, list):
            total = hackathons.count()
        else:
            total = len(hackathons)

        if total == 0:
            self.stdout.write(self.style.WARNING('No hackathons found to export'))
            return

        self.stdout.write(f'Found {total} hackathons (sorted {sort_desc})')

        # Export based on format
        if output_format == 'json':
            self.export_json(hackathons, output_file)
        else:  # csv
            self.export_csv(hackathons, output_file)

        self.stdout.write(self.style.SUCCESS(f'✓ Successfully exported to {output_file}'))

    def export_json(self, hackathons, output_file):
        """Export hackathons to JSON format"""
        data = []
        
        for hackathon in hackathons:
            data.append({
                'id': hackathon.id,
                'name': hackathon.name,
                'url': hackathon.url,
                'organizer': hackathon.organizer,
                'status': hackathon.status,
                'participants_count': hackathon.participants_count,
                'projects_count': hackathon.projects_count,
                'about_content': hackathon.about_content,
                'start_date': hackathon.start_date,
                'end_date': hackathon.end_date,
                'location': hackathon.location,
                'mode': hackathon.mode,
                'prizes': hackathon.prizes,
                'themes': hackathon.themes,
                'organizer_contact': hackathon.organizer_contact,
                'important_dates': hackathon.important_dates,
                'official_website': hackathon.official_website,
                'scraped_at': hackathon.scraped_at.isoformat() if hackathon.scraped_at else None,
                'updated_at': hackathon.updated_at.isoformat() if hackathon.updated_at else None,
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def export_csv(self, hackathons, output_file):
        """Export hackathons to CSV format"""
        fieldnames = [
            'id', 'name', 'url', 'organizer', 'status',
            'participants_count', 'projects_count',
            'about_content', 'start_date', 'end_date',
            'location', 'mode', 'prizes', 'themes',
            'organizer_contact', 'important_dates',
            'official_website', 'scraped_at', 'updated_at'
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for hackathon in hackathons:
                writer.writerow({
                    'id': hackathon.id,
                    'name': hackathon.name,
                    'url': hackathon.url,
                    'organizer': hackathon.organizer or '',
                    'status': hackathon.status or '',
                    'participants_count': hackathon.participants_count or '',
                    'projects_count': hackathon.projects_count or '',
                    'about_content': hackathon.about_content or '',
                    'start_date': hackathon.start_date or '',
                    'end_date': hackathon.end_date or '',
                    'location': hackathon.location or '',
                    'mode': hackathon.mode or '',
                    'prizes': hackathon.prizes or '',
                    'themes': hackathon.themes or '',
                    'organizer_contact': hackathon.organizer_contact or '',
                    'important_dates': hackathon.important_dates or '',
                    'official_website': hackathon.official_website or '',
                    'scraped_at': hackathon.scraped_at.isoformat() if hackathon.scraped_at else '',
                    'updated_at': hackathon.updated_at.isoformat() if hackathon.updated_at else '',
                })
