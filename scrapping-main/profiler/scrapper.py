from seleniumbase import Driver

# Create a custom, local directory for the UC Mode profile data.
# This folder will be created and configured by UC Mode the first time.
UC_PROFILE_PATH = r"~/.config/chromium/Profile 3/" 
CHROMIUM_BINARY_PATH = "/usr/bin/chromium"
driver = Driver(
    uc=True, # Activate Undetectable-Chromedriver Mode
    browser="chrome",
    binary_location=CHROMIUM_BINARY_PATH,
    user_data_dir=UC_PROFILE_PATH # Point to the profile folder
)

try:
    driver.uc_open_with_reconnect("https://www.example.com")
    # This profile will now retain data between sessions.
    print(driver.title)
finally:
    driver.quit()

# Note: In UC Mode, the profile folder inside the user_data_dir 
# is always named 'Default'. You only specify the main directory path.
