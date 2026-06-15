from django.core.management.base import BaseCommand
from contacts.models import Profile, Contact
import json
import csv
import os

class Command(BaseCommand):
    help = 'Export LinkedIn profiles to JSON and CSV file formats'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv', 'both'],
            default='both',
            help='Export format: json, csv, or both (default: both)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='linkedin_profiles',
            help='Output filename without extension (default: linkedin_profiles)'
        )
        parser.add_argument(
            '--with-contacts',
            action='store_true',
            help='Include linked contact email information if available'
        )

    def handle(self, *args, **options):
        format_type = options['format']
        output_name = options['output']
        with_contacts = options['with_contacts']
        
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("LinkedIn Profile Exporter"))
        self.stdout.write("="*70 + "\n")
        
        # Fetch all profiles
        if with_contacts:
            profiles = Profile.objects.select_related('contact').all()
        else:
            profiles = Profile.objects.all()
        
        count = profiles.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING("Warning: No profiles found in database"))
            return
        
        self.stdout.write(f"Found {count} profiles in database\n")
        
        # Export to JSON
        if format_type in ['json', 'both']:
            json_file = f"{output_name}.json"
            self._export_json(profiles, json_file, with_contacts)
            self.stdout.write(self.style.SUCCESS(f"Exported to {json_file}"))
        
        # Export to CSV
        if format_type in ['csv', 'both']:
            csv_file = f"{output_name}.csv"
            self._export_csv(profiles, csv_file, with_contacts)
            self.stdout.write(self.style.SUCCESS(f"Exported to {csv_file}"))
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(f"Total profiles exported: {count}")
        self.stdout.write("="*70)
    
    def _export_json(self, profiles, filename, with_contacts):
        """Export profiles to JSON"""
        data = []
        
        for profile in profiles:
            profile_dict = {
                'linkedin_url': profile.linkedin_url,
                'scraped_at': profile.scraped_at.isoformat() if profile.scraped_at else None,
            }
            
            if with_contacts and profile.contact:
                profile_dict['contact_email'] = profile.contact.email
                profile_dict['contact_name'] = profile.contact.name
            
            data.append(profile_dict)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _export_csv(self, profiles, filename, with_contacts):
        """Export profiles to CSV"""
        fieldnames = ['linkedin_url', 'scraped_at']
        
        if with_contacts:
            fieldnames.extend(['contact_email', 'contact_name'])
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for profile in profiles:
                row = {
                    'linkedin_url': profile.linkedin_url,
                    'scraped_at': profile.scraped_at.isoformat() if profile.scraped_at else '',
                }
                
                if with_contacts:
                    if profile.contact:
                        row['contact_email'] = profile.contact.email
                        row['contact_name'] = profile.contact.name or ''
                    else:
                        row['contact_email'] = ''
                        row['contact_name'] = ''
                
                writer.writerow(row)
