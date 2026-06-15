import json
import csv
from django.core.management.base import BaseCommand
from scraper.models import Competition


class Command(BaseCommand):
    help = """
    Export competitions to JSON or CSV format.
    
    This command exports all scraped competition data from the database
    to structured files for analysis, backup, or integration.
    
    SUPPORTED FORMATS:
      - JSON: Structured data with all fields including prizes
      - CSV: Tabular format for spreadsheet analysis
    
    USAGE:
    
      # Export to JSON
      python manage.py export_competitions --format json
      
      # Export to CSV
      python manage.py export_competitions --format csv
      
      # Export with custom filename
      python manage.py export_competitions --output my_competitions.csv
    
    EXAMPLES:
    
      # Export as JSON sorted by name
      python manage.py export_competitions --format json --sort name
      
      # Export as CSV sorted by registration count
      python manage.py export_competitions --format csv --sort registrations
      
      # Export to specific file
      python manage.py export_competitions --output exports/data.json
      
      # Export sorted by date (most recent first)
      python manage.py export_competitions --sort date
    
    SORTING OPTIONS:
      name           - Alphabetical by competition name
      date           - By scraped date (most recent first)
      organizer      - Alphabetical by organizer name
      registrations  - By registration count (highest first)
    
    EXPORTED FIELDS:
      - id, name, url, organizer
      - registration_count, impression_count
      - about_content, organizer_contact
      - important_dates, official_website
      - prizes (competition-specific field)
      - scraped_at, updated_at
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv'],
            default='json',
            help='Export format (json or csv)',
        )
        parser.add_argument(
            '--output',
            type=str,
            default='competitions_export',
            help='Output filename (without extension)',
        )
        parser.add_argument(
            '--sort',
            type=str,
            choices=['name', 'date', 'organizer', 'registrations'],
            default='date',
            help='Sort order for export (default: date - most recent first)',
        )

    def handle(self, *args, **options):
        export_format = options['format']
        output_file = options['output']
        sort_option = options['sort']
        
        # Ensure correct extension
        if not output_file.endswith(f'.{export_format}'):
            if '.' in output_file:
                output_file = output_file.rsplit('.', 1)[0]
            output_file = f'{output_file}.{export_format}'
        
        # Get competitions with sorting
        if sort_option == 'name':
            competitions = Competition.objects.all().order_by('name')
            sort_desc = "alphabetically by name"
        elif sort_option == 'organizer':
            competitions = Competition.objects.all().order_by('organizer', 'name')
            sort_desc = "by organizer"
        elif sort_option == 'registrations':
            # Get all and sort in Python for proper numeric sorting
            competitions = list(Competition.objects.all().order_by('-scraped_at'))
            competitions.sort(key=lambda x: int(x.registration_count or x.registered_count or '0') if (x.registration_count or x.registered_count or '0').replace(',', '').isdigit() else 0, reverse=True)
            sort_desc = "by registration count (highest first)"
        else:  # date (default)
            competitions = Competition.objects.all().order_by('-scraped_at')
            sort_desc = "by date (most recent first)"
        
        if not isinstance(competitions, list):
            count = competitions.count()
        else:
            count = len(competitions)
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No competitions found in database'))
            return
        
        self.stdout.write(f'Exporting {count} competitions (sorted {sort_desc})')
        
        if export_format == 'json':
            self.export_json(competitions, output_file)
        else:
            self.export_csv(competitions, output_file)
        
        self.stdout.write(self.style.SUCCESS(f'Exported {count} competitions to {output_file}'))

    def export_json(self, competitions, output_file):
        """Export to JSON format"""
        data = []
        for h in competitions:
            data.append({
                'id': h.id,
                'name': h.name,
                'url': h.url,
                'organizer': h.organizer,
                'registered_count': h.registered_count,
                'registration_count': h.registration_count,
                'impression_count': h.impression_count,
                'about_content': h.about_content,
                'organizer_contact': h.organizer_contact,
                'important_dates': h.important_dates,
                'official_website': h.official_website,
                'prizes': h.prizes,
                'scraped_at': h.scraped_at.isoformat() if h.scraped_at else None,
                'updated_at': h.updated_at.isoformat() if h.updated_at else None,
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def export_csv(self, competitions, output_file):
        """Export to CSV format"""
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                'ID',
                'Name',
                'URL',
                'Organizer',
                'Registered Count (Legacy)',
                'Registration Count',
                'Impression Count',
                'About Content',
                'Organizer Contact',
                'Important Dates',
                'Official Website',
                'Prizes',
                'Scraped At',
                'Updated At',
            ])
            
            # Write data
            for h in competitions:
                writer.writerow([
                    h.id,
                    h.name,
                    h.url,
                    h.organizer,
                    h.registered_count,
                    h.registration_count,
                    h.impression_count,
                    h.about_content,
                    h.organizer_contact,
                    h.important_dates,
                    h.official_website,
                    h.prizes,
                    h.scraped_at.isoformat() if h.scraped_at else '',
                    h.updated_at.isoformat() if h.updated_at else '',
                ])
