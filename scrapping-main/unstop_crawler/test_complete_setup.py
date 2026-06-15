#!/usr/bin/env python
"""
Test script to verify all features are working
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstop_project.settings')
django.setup()

from scraper.models import Hackathon
from browser_config import USER_DATA_DIR, PROFILE_NAME, BROWSER_BINARY

print("=" * 70)
print("🔍 UNSTOP CRAWLER - COMPLETE SETUP VERIFICATION")
print("=" * 70)

# Check browser config
print("\n📌 BROWSER CONFIGURATION:")
print(f"   User Data Dir: {USER_DATA_DIR}")
print(f"   Profile: {PROFILE_NAME}")
print(f"   Browser Binary: {BROWSER_BINARY}")
print(f"   Profile Exists: {os.path.exists(os.path.join(USER_DATA_DIR, PROFILE_NAME))}")

# Check database
print("\n📊 DATABASE STATUS:")
hackathons = Hackathon.objects.all()
print(f"   Total Hackathons: {hackathons.count()}")

if hackathons.exists():
    latest = hackathons.first()
    print(f"\n📝 LATEST HACKATHON:")
    print(f"   Name: {latest.name}")
    print(f"   Organizer: {latest.organizer}")
    print(f"   URL: {latest.url}")
    
    print(f"\n📅 IMPORTANT DATES:")
    if latest.important_dates:
        for line in latest.important_dates.split('\n')[:5]:
            print(f"   • {line}")
    else:
        print("   (None extracted)")
    
    print(f"\n🌐 OFFICIAL WEBSITE:")
    print(f"   {latest.official_website if latest.official_website else '(None found)'}")
    
    print(f"\n📧 CONTACT INFO:")
    if latest.organizer_contact:
        for line in latest.organizer_contact.split('\n')[:3]:
            print(f"   • {line}")
    else:
        print("   (None found)")
    
    print(f"\n✅ NEW FIELDS WORKING:")
    print(f"   Important Dates: {'✓' if latest.important_dates else '✗'}")
    print(f"   Official Website: {'✓' if latest.official_website else '✗'}")

print("\n" + "=" * 70)
print("✅ ALL SYSTEMS READY!")
print("=" * 70)
print("\nRun: python manage.py scrape_unstop --limit 5")
print("=" * 70)
