#!/usr/bin/env python3
"""
Fix Devfolio Organizer Names in Database
Replaces organizer names that are actually city names with proper hackathon names
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstop_project.settings')
django.setup()

from scraper.models import DevfolioHackathon

def fix_organizers():
    print("=" * 70)
    print("   FIX DEVFOLIO ORGANIZERS - Replace City Names with Hackathon Names")
    print("=" * 70)
    
    # Get all hackathons
    hackathons = DevfolioHackathon.objects.all()
    total = hackathons.count()
    
    if total == 0:
        print("\n❌ No Devfolio hackathons found in database.")
        return
    
    print(f"\n📊 Found {total} Devfolio hackathons in database")
    print("\n🔍 Checking for organizers that match location city...")
    
    fixed_count = 0
    skipped_count = 0
    
    for hackathon in hackathons:
        organizer = hackathon.organizer or ''
        location = hackathon.location or ''
        name = hackathon.name or ''
        
        # Check if organizer is likely a city name by comparing with location
        # If organizer appears in location, it's probably the city name
        needs_fix = False
        
        if organizer and location:
            # Check if organizer is the first part of location (likely the city)
            location_parts = location.split(',')
            if location_parts and organizer.strip() == location_parts[0].strip():
                needs_fix = True
        
        if needs_fix:
            # Replace organizer with hackathon name
            old_organizer = hackathon.organizer
            hackathon.organizer = name
            hackathon.save()
            
            fixed_count += 1
            print(f"\n✓ Fixed [{fixed_count}]: {name}")
            print(f"  Old organizer: {old_organizer} (was city name)")
            print(f"  New organizer: {name}")
            print(f"  Location: {location}")
        else:
            skipped_count += 1
    
    print("\n" + "=" * 70)
    print("   SUMMARY")
    print("=" * 70)
    print(f"✅ Fixed organizers: {fixed_count}")
    print(f"⏭  Already correct: {skipped_count}")
    print(f"📊 Total processed: {total}")
    
    if fixed_count > 0:
        print("\n✅ SUCCESS! Organizer names have been updated.")
        print("\n💡 Next steps:")
        print("   1. Verify organizers are correct:")
        print("      python manage.py export_devfolio --format json")
        print("   2. Export to Supabase:")
        print("      python manage.py export_to_supabase -d devfolio --update-existing")
    else:
        print("\n✓ All organizer names are already correct!")
    
    print("\n📝 Note: Some hackathons may still have city-like organizer names")
    print("   if the hosted_by field was null in the API. This is expected.")

if __name__ == "__main__":
    try:
        fix_organizers()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
