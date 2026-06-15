from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

"""
Browser configuration for Selenium scraping
Configure your Chromium/Chrome browser settings here
"""

# Chromium/Chrome user data directory
USER_DATA_DIR = "./chromium/"

# Profile name to use (check ~/.config/chromium/ for available profiles)
# Common profile names: "Default", "Profile 1", "Profile 2", etc.
PROFILE_NAME = "unstop"

# Browser binary location (for Chromium)
BROWSER_BINARY = "/usr/bin/chromium"

# User agent string (optional - leave as is for default)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# --- Main Automation Logic ---

# 1. Initialize ChromeOptions
options = Options()

# 2. Set the User Data Directory and Profile Directory
# This is the key step to load your existing profile, including cookies and login state.
options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
options.add_argument(f'--profile-directory={PROFILE_NAME}')

# 3. Specify the browser binary location
# This ensures Selenium launches the correct Chromium/Chrome version.
options.binary_location = BROWSER_BINARY

# 4. (Optional) Set a custom User-Agent
options.add_argument(f"user-agent={USER_AGENT}")

# 5. Initialize WebDriver
# NOTE: Ensure you have the corresponding ChromeDriver executable installed 
# and accessible, or use a tool like 'webdriver-manager'.
try:
    # On modern Selenium (4.6+), we use Service for the driver executable path (if needed)
    # If your chromedriver is in PATH, you can often omit the 'service' argument.
    
    # Assuming ChromeDriver is in your system PATH or using Service:
    # driver_service = Service('/path/to/your/chromedriver') # Uncomment and set path if necessary
    
    driver = webdriver.Chrome(options=options)
    
    print(f"✅ Successfully opened Chromium with profile: **{PROFILE_NAME}**")
    
    # 6. Perform automation actions
    driver.get("https://example.com") # Change this to your target URL
    print(f"Current URL: {driver.current_url}")
    
    # Add your scraping/automation code here...
    
    # 7. Keep the browser open briefly (for demonstration)
    import time
    time.sleep(10)

finally:
    # 8. Close the browser session
    if 'driver' in locals() and driver:
        driver.quit()
        print("Browser closed.")
