from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.binary_location = "/usr/bin/chromium"

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

url = "https://devfolio.co/hackathons/open"
print(f"Fetching: {url}")
driver.get(url)

print("Waiting 10 seconds for page to load...")
time.sleep(10)

print("\nExtracting URLs...")
soup = BeautifulSoup(driver.page_source, 'html.parser')

# Save HTML for inspection
with open('devfolio_page.html', 'w') as f:
    f.write(driver.page_source)

# Find all links
links = soup.find_all('a', href=True)
hackathon_urls = []

for link in links:
    href = link['href']
    if href.startswith('/hackathons/') and href.count('/') == 2:
        if not any(x in href for x in ['/open', '/past', '/upcoming']):
            full_url = f"https://devfolio.co{href}"
            if full_url not in hackathon_urls:
                hackathon_urls.append(full_url)
                print(f"Found: {full_url}")

print(f"\nTotal URLs found: {len(hackathon_urls)}")

driver.quit()
