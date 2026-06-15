#!/usr/bin/env python3
"""
Analyze Devfolio page structure to understand how to scrape it
"""
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import browser_config

def analyze_devfolio():
    print("Analyzing Devfolio page structure...")
    
    # Setup Chrome options
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f"user-agent={browser_config.USER_AGENT}")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        url = "https://devfolio.co/hackathons/open"
        print(f"\nLoading: {url}")
        driver.get(url)
        
        # Wait for page load
        print("Waiting for content to load...")
        time.sleep(10)
        
        # Try scrolling to trigger lazy loading
        print("Scrolling page...")
        for i in range(3):
            driver.execute_script("window.scrollBy(0, 1000)")
            time.sleep(2)
        
        # Save HTML
        html = driver.page_source
        with open('devfolio_analysis.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"Saved HTML to devfolio_analysis.html ({len(html)} bytes)")
        
        # Analysis
        print("\n=== PAGE ANALYSIS ===")
        print(f"Title: {driver.title}")
        print(f"URL: {driver.current_url}")
        
        # Check for common patterns
        selectors = [
            ('a[href*="/hackathons/"]', By.CSS_SELECTOR),
            ('div[class*="Card"]', By.CSS_SELECTOR),
            ('div[class*="card"]', By.CSS_SELECTOR),
            ('article', By.TAG_NAME),
            ('[data-testid*="card"]', By.CSS_SELECTOR),
        ]
        
        print("\nSearching for hackathon containers...")
        for selector, by_type in selectors:
            try:
                elements = driver.find_elements(by_type, selector)
                if elements:
                    print(f"  ✓ {selector}: {len(elements)} found")
                    if len(elements) > 0:
                        el = elements[0]
                        print(f"    Sample: class='{el.get_attribute('class')}', href='{el.get_attribute('href')}'")
            except Exception as e:
                pass
        
        # Get all links
        print("\nExtracting all links with 'hackathons' in href...")
        links = driver.execute_script('''
            const allLinks = Array.from(document.querySelectorAll('a'));
            return allLinks
                .map(a => a.href)
                .filter(href => href && href.includes('/hackathons/'))
                .filter(href => !href.endsWith('/hackathons/open') && 
                               !href.endsWith('/hackathons/past') && 
                               !href.endsWith('/hackathons/upcoming'));
        ''')
        
        unique_links = list(set(links))
        print(f"Found {len(unique_links)} unique hackathon URLs")
        if unique_links:
            print("\nSample URLs:")
            for link in unique_links[:10]:
                print(f"  {link}")
        
        # Check page text
        print("\nSearching for text patterns...")
        page_text = driver.find_element(By.TAG_NAME, 'body').text
        if 'No hackathons' in page_text or 'no hackathons' in page_text:
            print("  ! Page says 'No hackathons'")
        if 'loading' in page_text.lower()[:500]:
            print("  ! Page appears to be loading")
        
        # Check for React/Next.js data
        print("\nChecking framework...")
        try:
            next_data_el = driver.find_element(By.ID, '__NEXT_DATA__')
            if next_data_el:
                print("  ✓ Next.js detected")
                data = json.loads(next_data_el.get_attribute('textContent'))
                print(f"  Props keys: {list(data.get('props', {}).keys())}")
                
                # Try to find hackathons in props
                props = data.get('props', {})
                if 'pageProps' in props:
                    page_props = props['pageProps']
                    print(f"  PageProps keys: {list(page_props.keys())}")
                    
                    # Look for hackathons data
                    for key in page_props:
                        val = page_props[key]
                        if isinstance(val, list) and len(val) > 0:
                            print(f"    {key}: {len(val)} items")
                            if len(val) > 0 and isinstance(val[0], dict):
                                print(f"      Sample keys: {list(val[0].keys())[:10]}")
        except Exception as e:
            print(f"  No Next.js data found: {e}")
        
        input("\nPress Enter to close browser...")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_devfolio()
