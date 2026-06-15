"""
Browser configuration for Selenium scraping
Configure your Chromium/Chrome browser settings here
"""

# Chromium/Chrome user data directory
USER_DATA_DIR = "/home/sonu/.config/chromium"

# Profile name to use (check ~/.config/chromium/ for available profiles)
# Common profile names: "Default", "Profile 1", "Profile 2", etc.
PROFILE_NAME = "Profile 1"

# Browser binary location
# Common locations:
# - Chromium: /usr/bin/chromium or /usr/bin/chromium-browser
# - Chrome: /usr/bin/google-chrome or /usr/bin/google-chrome-stable
BROWSER_BINARY = "/usr/bin/chromium"

# User agent string (optional - leave as is for default)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
