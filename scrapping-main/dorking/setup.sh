#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Create superuser if needed
echo "Creating superuser for Django admin..."
python manage.py createsuperuser

echo ""
echo "Setup complete! You can now:"
echo "  1. Start the server: python manage.py runserver"
echo "  2. Access admin: http://127.0.0.1:8000/admin"
echo "  3. Import dorks: python manage.py import_json example_import.json"
echo "  4. Crawl: python manage.py crawl_dorks --query 'your query' --pages 5"
echo "  5. Export: python manage.py export_json --output results.json --pretty"
