from django.core.management.base import BaseCommand
from crawler.models import DorkQuery
import json

class Command(BaseCommand):
    help = 'Import dork queries from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            'file',
            type=str,
            help='JSON file to import',
        )

    def handle(self, *args, **options):
        input_file = options['file']
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both single query and multiple queries format
            if 'dork_queries' in data:
                queries = data['dork_queries']
            elif 'dork_query' in data:
                queries = [data['dork_query']]
            else:
                # Assume it's a list of queries
                queries = data if isinstance(data, list) else [data]
            
            created_count = 0
            updated_count = 0
            
            for query_data in queries:
                query_text = query_data.get('query')
                if not query_text:
                    continue
                
                dork_query, created = DorkQuery.objects.update_or_create(
                    query=query_text,
                    defaults={
                        'description': query_data.get('description', ''),
                        'is_active': query_data.get('is_active', True),
                    }
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            self.stdout.write(self.style.SUCCESS(f'Import completed!'))
            self.stdout.write(f'  Created: {created_count}')
            self.stdout.write(f'  Updated: {updated_count}')
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {input_file}'))
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON: {str(e)}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
