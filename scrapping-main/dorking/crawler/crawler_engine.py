import time
import random
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from django.utils import timezone
from .models import DorkQuery, CrawledLink

class GoogleDorkCrawler:
    def __init__(self, headless=True, use_profile=False):
        self.driver = None
        self.headless = headless
        self.use_profile = use_profile
        self.db_lock = Lock()
        
    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        chrome_options = Options()
        
        # Use existing Chromium profile only if specified
        if self.use_profile:
            chrome_options.add_argument(f"--user-data-dir=/home/sonu/.config/chromium")
            chrome_options.add_argument("--profile-directory=Profile 3")
        else:
            # Use temporary profile for multi-threading
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-default-browser-check")
        
        # Headless mode
        if self.headless:
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--disable-gpu")
        
        # Anti-detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Additional stealth options
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # User agent
        user_agents = [
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        ]
        chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Override webdriver detection
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                window.chrome = {
                    runtime: {}
                };
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            '''
        })
        
    def human_delay(self, min_delay=2, max_delay=5):
        """Random delay to mimic human behavior"""
        time.sleep(random.uniform(min_delay, max_delay))
        
    def scroll_slowly(self):
        """Scroll page slowly to mimic human behavior"""
        try:
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            current_position = 0
            scroll_step = random.randint(300, 500)
            
            while current_position < scroll_height:
                current_position += scroll_step
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                time.sleep(random.uniform(0.2, 0.5))
        except Exception:
            pass
    
    def crawl_single_page(self, dork_query, page_number):
        """
        Crawl a single page of search results
        
        Args:
            dork_query: DorkQuery model instance
            page_number: Page number to crawl (1-indexed)
        
        Returns:
            list: Crawled links for this page
        """
        try:
            if not self.driver:
                self.setup_driver()
            
            start = (page_number - 1) * 10
            search_url = f"https://www.google.com/search?q={quote_plus(dork_query.query)}&start={start}"
            
            print(f"[Page {page_number}] Crawling...")
            self.driver.get(search_url)
            
            # Random delay
            self.human_delay(2, 4)
            
            # Scroll to load all results
            self.scroll_slowly()
            
            # Wait for results to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "search"))
                )
            except TimeoutException:
                print(f"[Page {page_number}] Timeout waiting for results")
                return []
            
            # Check for CAPTCHA or unusual activity detection
            if "unusual traffic" in self.driver.page_source.lower():
                print(f"[Page {page_number}] Google detected unusual traffic!")
                return []
            
            # Extract search results
            page_results = self.extract_results(dork_query, page_number)
            
            return page_results
            
        except Exception as e:
            print(f"[Page {page_number}] Error: {str(e)}")
            return []
    
    def search_google(self, dork_query, max_pages=10, threads=1):
        """
        Search Google with dork query and collect results
        
        Args:
            dork_query: DorkQuery model instance
            max_pages: Maximum number of pages to crawl (default 10)
            threads: Number of concurrent threads (default 1)
        """
        try:
            results = []
            empty_pages_count = 0
            max_consecutive_empty = 3
            
            if threads > 1:
                # Multi-threaded crawling
                print(f"Starting multi-threaded crawl with {threads} threads")
                print(f"Query: {dork_query.query}")
                
                # Create separate crawler instances for each thread
                def crawl_page_worker(page_num):
                    crawler = GoogleDorkCrawler(headless=self.headless, use_profile=False)
                    try:
                        page_results = crawler.crawl_single_page(dork_query, page_num)
                        return page_num, page_results
                    finally:
                        crawler.close()
                
                with ThreadPoolExecutor(max_workers=threads) as executor:
                    # Submit pages in batches to check for empty results
                    batch_size = threads
                    page = 1
                    
                    while page <= max_pages:
                        # Submit batch of pages
                        batch_end = min(page + batch_size, max_pages + 1)
                        futures = {executor.submit(crawl_page_worker, p): p for p in range(page, batch_end)}
                        
                        batch_had_results = False
                        for future in as_completed(futures):
                            page_num, page_results = future.result()
                            
                            if page_results:
                                with self.db_lock:
                                    results.extend(page_results)
                                batch_had_results = True
                                print(f"[Page {page_num}] ✓ Found {len(page_results)} results")
                            else:
                                print(f"[Page {page_num}] ✗ No results found")
                        
                        # Check if we should stop (3 consecutive empty pages)
                        if not batch_had_results:
                            empty_pages_count += batch_size
                            if empty_pages_count >= max_consecutive_empty:
                                print(f"\n⚠ Stopping: {empty_pages_count} consecutive empty pages")
                                break
                        else:
                            empty_pages_count = 0
                        
                        page += batch_size
                        
                        # Delay between batches
                        if page <= max_pages:
                            time.sleep(random.uniform(2, 4))
            else:
                # Single-threaded crawling
                print(f"Starting single-threaded crawl")
                print(f"Query: {dork_query.query}")
                
                if not self.driver:
                    self.setup_driver()
                
                for page in range(1, max_pages + 1):
                    page_results = self.crawl_single_page(dork_query, page)
                    
                    if page_results:
                        results.extend(page_results)
                        empty_pages_count = 0
                        print(f"[Page {page}] ✓ Found {len(page_results)} results")
                    else:
                        empty_pages_count += 1
                        print(f"[Page {page}] ✗ No results found")
                        
                        if empty_pages_count >= max_consecutive_empty:
                            print(f"\n⚠ Stopping: {empty_pages_count} consecutive empty pages")
                            break
                    
                    # Delay between pages
                    if page < max_pages:
                        self.human_delay(3, 6)
            
            # Update last crawled time
            dork_query.last_crawled = timezone.now()
            dork_query.save()
            
            print(f"\n✓ Total crawled: {len(results)} new links")
            return results
            
        except Exception as e:
            print(f"Error during crawling: {str(e)}")
            return []
    
    def extract_results(self, dork_query, page_number):
        """Extract search results from current page"""
        results = []
        
        try:
            # Try finding links with h3 (main results)
            result_links = self.driver.find_elements(By.CSS_SELECTOR, "a.zReHs, a:has(h3)")
            
            if not result_links:
                # Fallback to div.g containers
                search_results = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
                
                if not search_results:
                    # Debug: save page source
                    with open(f'debug_page_{page_number}.html', 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    return results
                
                # Process div.g containers
                for index, result in enumerate(search_results, 1):
                    try:
                        # Extract link
                        url = None
                        link_element = None
                        
                        try:
                            link_element = result.find_element(By.CSS_SELECTOR, "a:has(h3)")
                            url = link_element.get_attribute("href")
                        except NoSuchElementException:
                            links = result.find_elements(By.TAG_NAME, "a")
                            for link in links:
                                href = link.get_attribute("href")
                                if href and href.startswith("http") and "google.com" not in href:
                                    url = href
                                    link_element = link
                                    break
                        
                        if not url or "google.com" in url:
                            continue
                        
                        # Extract title
                        title = ""
                        try:
                            title_element = result.find_element(By.CSS_SELECTOR, "h3")
                            title = title_element.text
                        except NoSuchElementException:
                            if link_element:
                                title = link_element.text[:100]
                        
                        # Extract snippet
                        snippet = ""
                        for selector in ["div.VwiC3b", "span.aCOpRe", "div[style*='-webkit-line-clamp']"]:
                            try:
                                snippet_element = result.find_element(By.CSS_SELECTOR, selector)
                                snippet = snippet_element.text
                                if snippet:
                                    break
                            except NoSuchElementException:
                                continue
                        
                        # Save to database (with lock for thread safety)
                        with self.db_lock:
                            crawled_link, created = CrawledLink.objects.get_or_create(
                                dork_query=dork_query,
                                url=url,
                                defaults={
                                    'title': title,
                                    'snippet': snippet,
                                    'position': index,
                                    'page_number': page_number
                                }
                            )
                        
                        if created:
                            results.append(crawled_link)
                            
                    except Exception:
                        continue
            else:
                # Process links directly
                for index, link_element in enumerate(result_links, 1):
                    try:
                        url = link_element.get_attribute("href")
                        
                        # Skip invalid or Google URLs
                        if not url or not url.startswith("http") or "google.com" in url:
                            continue
                        
                        # Extract title from h3
                        title = ""
                        try:
                            title_element = link_element.find_element(By.TAG_NAME, "h3")
                            title = title_element.text
                        except NoSuchElementException:
                            title = link_element.text[:100] if link_element.text else ""
                        
                        # Extract snippet from nearby elements
                        snippet = ""
                        try:
                            parent = link_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'g')]")
                            snippet_elements = parent.find_elements(By.CSS_SELECTOR, "div.VwiC3b, span.aCOpRe, div[style*='-webkit-line-clamp']")
                            if snippet_elements:
                                snippet = snippet_elements[0].text
                        except Exception:
                            pass
                        
                        # Save to database (with lock for thread safety)
                        with self.db_lock:
                            crawled_link, created = CrawledLink.objects.get_or_create(
                                dork_query=dork_query,
                                url=url,
                                defaults={
                                    'title': title,
                                    'snippet': snippet,
                                    'position': index,
                                    'page_number': page_number
                                }
                            )
                        
                        if created:
                            results.append(crawled_link)
                            
                    except Exception:
                        continue
                    
        except Exception as e:
            print(f"  Error extracting results: {str(e)}")
        
        return results
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
            self.driver = None
