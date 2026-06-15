#!/bin/bash

# Clean Chrome Profile Locks
# Use this when scraper hangs or fails to start with "profile in use" error

echo "Cleaning Chrome profile locks..."

# Clean profile directory
rm -f profile/SingletonLock profile/SingletonSocket profile/SingletonCookie 2>/dev/null
echo "✓ Cleaned ./profile"

# Clean profile2 directory  
rm -f profile3/SingletonLock profile3/SingletonSocket profile3/SingletonCookie 2>/dev/null
echo "✓ Cleaned ./profile3"

# Clean profile3-5 if they exist
for i in {3..5}; do
    if [ -d "profile$i" ]; then
        rm -f profile$i/SingletonLock profile$i/SingletonSocket profile$i/SingletonCookie 2>/dev/null
        echo "✓ Cleaned ./profile$i"
    fi
done

echo ""
echo "All Chrome locks cleaned! You can now run scrapers."
