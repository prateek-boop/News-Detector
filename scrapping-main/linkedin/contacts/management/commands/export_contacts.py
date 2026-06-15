from django.core.management.base import BaseCommand
from contacts.models import Contact
import json
import csv
import os

class Command(BaseCommand):
    help = 'Export contacts to JSON and CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv', 'both'],
            default='both',
            help='Export format (json, csv, or both)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='contacts_export',
            help='Output filename (without extension)'
        )

    def handle(self, *args, **options):
        format_type = options['format']
        output_name = options['output']
        
        contacts = Contact.objects.all().values('id', 'name', 'email', 'created_at', 'updated_at')
        contact_list = list(contacts)
        
        if not contact_list:
            self.stdout.write(self.style.WARNING("No contacts found in database"))
            return
        
        exported_files = []
        
        if format_type in ['json', 'both']:
            json_file = f"{output_name}.json"
            with open(json_file, 'w') as f:
                json.dump(contact_list, f, indent=2, default=str)
            exported_files.append(json_file)
            self.stdout.write(self.style.SUCCESS(f"✓ Exported to {json_file}"))
        
        if format_type in ['csv', 'both']:
            csv_file = f"{output_name}.csv"
            with open(csv_file, 'w', newline='') as f:
                if contact_list:
                    writer = csv.DictWriter(f, fieldnames=contact_list[0].keys())
                    writer.writeheader()
                    writer.writerows(contact_list)
            exported_files.append(csv_file)
            self.stdout.write(self.style.SUCCESS(f"✓ Exported to {csv_file}"))
        
        self.stdout.write(f"\nTotal contacts exported: {len(contact_list)}")
