#!/usr/bin/env python3
"""
Update Devfolio records with complete social links
Re-scrapes data from API to get all social connections
"""

import os
import sys
import django
import requests
import time

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unstop_project.settings')
django.setup()

from scraper.models import DevfolioHackathon

def update_social_links():
    print("=" * 70)
    print("   UPDATE DEVFOLIO SOCIAL LINKS - Add Complete Social Connections")
    print("=" * 70)
    
    # Fetch fresh data from API
    api_url = "https://api.devfolio.co/api/search/hackathons"
    
    statuses = ['application_open', 'upcoming', 'past']
    all_hackathons_data = {}
    
    print("\n🔍 Fetching latest data from Devfolio API...")
    
    for status in statuses:
        print(f"\n  Fetching {status} hackathons...")
        from_index = 0
        page_size = 50
        
        while True:
            payload = {"type": status, "from": from_index, "size": page_size}
            headers = {'Content-Type': 'application/json'}
            
            try:
                response = requests.post(api_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                hits = data.get('hits', {}).get('hits', [])
                if not hits:
                    break
                
                for hit in hits:
                    source = hit.get('_source', {})
                    slug = source.get('slug')
                    if slug:
                        all_hackathons_data[slug] = source
                
                total = data.get('hits', {}).get('total', {}).get('value', 0)
                print(f"    Fetched {len(all_hackathons_data)}/{total}...", end='\r')
                
                if len(all_hackathons_data) >= total:
                    break
                
                from_index += page_size
                time.sleep(0.3)
                
            except Exception as e:
                print(f"\n    Error: {e}")
                break
    
    print(f"\n\n✅ Fetched {len(all_hackathons_data)} hackathons from API")
    
    # Update database records
    print("\n🔄 Updating database with complete social links...")
    
    updated_count = 0
    skipped_count = 0
    
    for hackathon in DevfolioHackathon.objects.all():
        # Extract slug from URL
        url = hackathon.url or ''
        if '.devfolio.co' in url:
            slug = url.split('//')[1].split('.')[0] if '//' in url else ''
        else:
            slug = ''
        
        if slug and slug in all_hackathons_data:
            source = all_hackathons_data[slug]
            settings = source.get('hackathon_setting', {})
            
            # Build comprehensive contact info
            contact_parts = []
            
            # Email
            if settings.get('contact_email'):
                contact_parts.append(f"Email: {settings['contact_email']}")
            
            # Social Media Links (in order of importance)
            if settings.get('twitter'):
                contact_parts.append(f"Twitter: {settings['twitter']}")
            
            if settings.get('linkedin'):
                contact_parts.append(f"LinkedIn: {settings['linkedin']}")
            
            if settings.get('discord'):
                contact_parts.append(f"Discord: {settings['discord']}")
            
            if settings.get('telegram'):
                contact_parts.append(f"Telegram: {settings['telegram']}")
            
            if settings.get('facebook'):
                contact_parts.append(f"Facebook: {settings['facebook']}")
            
            if settings.get('instagram'):
                contact_parts.append(f"Instagram: {settings['instagram']}")
            
            if settings.get('youtube'):
                contact_parts.append(f"YouTube: {settings['youtube']}")
            
            if settings.get('github'):
                contact_parts.append(f"GitHub: {settings['github']}")
            
            new_contact = '\n'.join(contact_parts) if contact_parts else None
            
            # Update if there's new information
            if new_contact and new_contact != hackathon.organizer_contact:
                old_contact = hackathon.organizer_contact or '(empty)'
                hackathon.organizer_contact = new_contact
                hackathon.save()
                
                updated_count += 1
                if updated_count <= 5:  # Show first 5 examples
                    print(f"\n✓ Updated [{updated_count}]: {hackathon.name}")
                    print(f"  Old: {old_contact[:80]}...")
                    print(f"  New: {new_contact[:80]}...")
                elif updated_count % 50 == 0:
                    print(f"  Progress: {updated_count} updated...", end='\r')
            else:
                skipped_count += 1
        else:
            skipped_count += 1
    
    print("\n" + "=" * 70)
    print("   SUMMARY")
    print("=" * 70)
    print(f"✅ Updated with new social links: {updated_count}")
    print(f"⏭  No changes needed: {skipped_count}")
    print(f"📊 Total processed: {updated_count + skipped_count}")
    
    if updated_count > 0:
        print("\n✅ SUCCESS! Social links have been updated.")
        print("\n💡 Next steps:")
        print("   1. Verify social links are complete:")
        print("      python manage.py export_devfolio --format json")
        print("   2. Export to Supabase:")
        print("      python manage.py export_to_supabase -d devfolio --update-existing")
    else:
        print("\n✓ All social links are already up to date!")

if __name__ == "__main__":
    try:
        update_social_links()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
