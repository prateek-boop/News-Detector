from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from browser_config import BROWSER_BINARY

chrome_options = Options()
chrome_options.binary_location = BROWSER_BINARY
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")

driver = webdriver.Chrome(options=chrome_options)
driver.get("https://hackthetrack.devpost.com")
time.sleep(5)

# Scroll to load all content
for _ in range(3):
    driver.execute_script("window.scrollBy(0, 1000);")
    time.sleep(1)

soup = BeautifulSoup(driver.page_source, 'html.parser')

# Find sponsors section
sponsors_section = soup.find(id='challenge-sponsors-side')
print("Sponsors section found:", sponsors_section is not None)

if sponsors_section:
    print("\n=== SPONSORS SECTION HTML ===")
    print(sponsors_section.prettify()[:1000])
    
    # Find all links
    links = sponsors_section.find_all('a', href=True)
    print(f"\n=== FOUND {len(links)} LINKS ===")
    for link in links:
        href = link.get('href', '')
        print(f"  - {href}")

driver.quit()
