import time
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from browser_config import BROWSER_BINARY

url = "https://aethra-ideathon-2025.devpost.com"

chrome_options = Options()
chrome_options.binary_location = BROWSER_BINARY
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=chrome_options)

try:
    print(f"Fetching: {url}")
    driver.get(url)
    time.sleep(5)
    
    # Scroll
    for _ in range(3):
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(1)
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(2)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    print("\n=== CHECKING SIDEBAR ===")
    sidebar = soup.find(id='challenge-sponsors-side')
    if sidebar:
        print("Found sidebar")
        
        # Get all images with alt
        print("\n--- Sponsor Images ---")
        imgs = sidebar.find_all('img', alt=True)
        for i, img in enumerate(imgs):
            print(f"{i+1}. Alt: {img.get('alt')}")
            print(f"   Src: {img.get('src')}")
        
        # Get all links
        print("\n--- Sponsor Links ---")
        links = sidebar.find_all('a', href=True)
        for i, link in enumerate(links):
            print(f"{i+1}. Href: {link.get('href')}")
            print(f"   Text: {link.get_text(strip=True)}")
        
        # Get sidebar text
        print("\n--- Sidebar Full Text ---")
        print(sidebar.get_text()[:500])
    
    print("\n\n=== CHECKING TITLE ===")
    title = soup.find('title')
    if title:
        print(f"Title: {title.get_text()}")
    
    print("\n\n=== CHECKING PAGE TEXT FOR ORGANIZER ===")
    page_text = soup.get_text()
    
    # Search for patterns
    patterns = [
        (r'(?:hosted|organized|presented|powered)\s+by\s+([A-Z][A-Za-z0-9\s&.]+?)(?:\.|,|\n|$)', 'Hosted/Organized by'),
        (r'Organizer:\s*([A-Z][A-Za-z0-9\s&.]+?)(?:\.|,|\n|$)', 'Organizer:'),
    ]
    
    for pattern, desc in patterns:
        matches = re.findall(pattern, page_text, re.IGNORECASE)
        if matches:
            print(f"\n{desc} pattern found:")
            for match in matches[:3]:
                print(f"  - {match}")
    
finally:
    driver.quit()
