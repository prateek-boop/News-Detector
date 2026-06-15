from seleniumbase import Driver
from time import sleep
# 1. Define a path to a NEW, DEDICATED folder for UC Mode profile data.
#    (It's best to keep this outside of the regular Chrome User Data folder)
UC_PROFILE_PATH = "./profile" 
CHROMIUM_BINARY_PATH = "/usr/bin/chromium" 

# 2. On the FIRST RUN, this folder will be created and configured 
#    by undetected-chromedriver.
driver = Driver(
    browser="chrome", 
    uc=True,
    binary_location=CHROMIUM_BINARY_PATH,
    user_data_dir=UC_PROFILE_PATH 
)
sleep(300)
