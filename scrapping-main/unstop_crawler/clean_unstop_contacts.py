#!/usr/bin/env python3
"""
Clean up Unstop support numbers from organizer_contact field
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstop_project.settings')
django.setup()

from scraper.models import Hackathon

def clean_unstop_numbers():
    """Remove Unstop support numbers from contact fields"""
    
    unstop_numbers = [
        '9311777388',
        '93117 77388',
        '+91-9311777388',
        '+919311777388',
        '93 117 77388',
    ]
    
    print("="*70)
    print("  Cleaning Unstop Support Numbers from Database")
    print("="*70)
    
    # Find hackathons with the Unstop number
    affected = []
    
    for hackathon in Hackathon.objects.all():
        if hackathon.organizer_contact:
            contact = hackathon.organizer_contact
            
            # Check if it contains Unstop support number
            has_unstop_number = False
            for num in unstop_numbers:
                clean_num = num.replace('-', '').replace('+', '').replace(' ', '')
                clean_contact = contact.replace('-', '').replace('+', '').replace(' ', '')
                
                if clean_num in clean_contact:
                    has_unstop_number = True
                    break
            
            if has_unstop_number:
                affected.append(hackathon)
    
    print(f"\nFound {len(affected)} hackathons with Unstop support number")
    
    if not affected:
        print("\n✓ Database is clean!")
        return
    
    print("\nAffected hackathons:")
    for h in affected[:10]:  # Show first 10
        print(f"  - {h.name}")
    if len(affected) > 10:
        print(f"  ... and {len(affected) - 10} more")
    
    # Ask for confirmation
    print("\n" + "="*70)
    response = input(f"\nClear contact info for these {len(affected)} hackathons? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    # Clear the contact info
    cleaned = 0
    for hackathon in affected:
        hackathon.organizer_contact = ""
        hackathon.save()
        cleaned += 1
    
    print(f"\n✓ Cleaned {cleaned} hackathons")
    print("\nThese hackathons now have empty contact info.")
    print("You can re-run update_unstop to try extracting correct contacts.")

if __name__ == "__main__":
    clean_unstop_numbers()
