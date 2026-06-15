from django.core.management.base import BaseCommand
from django.core.serializers import serialize
from crawler.models import DorkQuery, CrawledLink
import json

class Command(BaseCommand):
    help = 'Export dork queries and crawled links to JSON'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='export.json',
            help='Output JSON file path (default: export.json)',
        )
        parser.add_argument(
            '--query',
            type=str,
            help='Export links for specific dork query only',
        )
        parser.add_argument(
            '--pretty',
            action='store_true',
            help='Pretty print JSON output',
        )

    def handle(self, *args, **options):
        output_file = options['output']
        
        if options['query']:
            # Export specific query
            try:
                dork_query = DorkQuery.objects.get(query=options['query'])
                links = CrawledLink.objects.filter(dork_query=dork_query)
                
                data = {
                    'dork_query': {
                        'query': dork_query.query,
                        'description': dork_query.description,
                        'last_crawled': dork_query.last_crawled.isoformat() if dork_query.last_crawled else None,
                        'created_at': dork_query.created_at.isoformat(),
                    },
                    'links': [
                        {
                            'url': link.url,
                            'title': link.title,
                            'snippet': link.snippet,
                            'page_number': link.page_number,
                            'position': link.position,
                            'found_at': link.found_at.isoformat(),
                        }
                        for link in links
                    ],
                    'total_links': links.count()
                }
                
            except DorkQuery.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Dork query not found: {options["query"]}'))
                return
                
        else:
            # Export all queries and links
            dork_queries = DorkQuery.objects.all()
            
            data = {
                'dork_queries': [],
                'total_queries': dork_queries.count(),
                'total_links': CrawledLink.objects.count()
            }
            
            for dork_query in dork_queries:
                links = dork_query.links.all()
                
                query_data = {
                    'query': dork_query.query,
                    'description': dork_query.description,
                    'is_active': dork_query.is_active,
                    'last_crawled': dork_query.last_crawled.isoformat() if dork_query.last_crawled else None,
                    'created_at': dork_query.created_at.isoformat(),
                    'links': [
                        {
                            'url': link.url,
                            'title': link.title,
                            'snippet': link.snippet,
                            'page_number': link.page_number,
                            'position': link.position,
                            'found_at': link.found_at.isoformat(),
                        }
                        for link in links
                    ],
                    'link_count': links.count()
                }
                
                data['dork_queries'].append(query_data)
        
        # Write to file
        indent = 2 if options['pretty'] else None
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        
        self.stdout.write(self.style.SUCCESS(f'Exported to {output_file}'))
        
        if options['query']:
            self.stdout.write(f"  Query: {options['query']}")
            self.stdout.write(f"  Links: {data['total_links']}")
        else:
            self.stdout.write(f"  Total Queries: {data['total_queries']}")
            self.stdout.write(f"  Total Links: {data['total_links']}")
