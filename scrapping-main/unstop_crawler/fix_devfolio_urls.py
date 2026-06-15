#!/usr/bin/env python3
"""
Fix Devfolio URLs in database
Converts old format: https://devfolio.co/hackathons/ethindia
To new format: https://ethindia.devfolio.co/overview
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstop_project.settings')
django.setup()

from scraper.models import DevfolioHackathon
import re

def fix_urls():
    print("=" * 70)
    print("   FIX DEVFOLIO URLs - Convert to Correct Format")
    print("=" * 70)
    
    # Pattern to match old URLs
    old_pattern = re.compile(r'https://devfolio\.co/hackathons/(.+)')
    
    # Get all hackathons
    hackathons = DevfolioHackathon.objects.all()
    total = hackathons.count()
    
    if total == 0:
        print("\n❌ No Devfolio hackathons found in database.")
        return
    
    print(f"\n📊 Found {total} Devfolio hackathons in database")
    print("\n🔍 Checking for URLs that need fixing...")
    
    fixed_count = 0
    skipped_count = 0
    
    for hackathon in hackathons:
        old_url = hackathon.url
        
        # Check if URL matches old format
        match = old_pattern.match(old_url)
        
        if match:
            slug = match.group(1)
            new_url = f"https://{slug}.devfolio.co/overview"
            
            # Update the URL
            hackathon.url = new_url
            hackathon.save()
            
            fixed_count += 1
            print(f"✓ Fixed [{fixed_count}]: {hackathon.name}")
            print(f"  Old: {old_url}")
            print(f"  New: {new_url}")
        else:
            skipped_count += 1
            if skipped_count <= 3:  # Show first 3 examples
                print(f"⏭  Skipped: {hackathon.name} (already correct)")
                print(f"   URL: {old_url}")
    
    print("\n" + "=" * 70)
    print("   SUMMARY")
    print("=" * 70)
    print(f"✅ Fixed URLs: {fixed_count}")
    print(f"⏭  Already correct: {skipped_count}")
    print(f"📊 Total processed: {total}")
    
    if fixed_count > 0:
        print("\n✅ SUCCESS! URLs have been updated in the database.")
        print("\n💡 Next steps:")
        print("   1. Verify URLs are correct:")
        print("      python manage.py export_devfolio --format json")
        print("   2. Export to Supabase:")
        print("      python manage.py export_to_supabase -d devfolio --update-existing")
    else:
        print("\n✓ All URLs are already in the correct format!")

if __name__ == "__main__":
    try:
        fix_urls()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
