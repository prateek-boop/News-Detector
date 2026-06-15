from seleniumbase import SB
import time
import re
import json
import csv

def extract_linkedin_links():
    # SeleniumBase with UC mode and existing Chrome profile - PROPER WAY
    with SB(uc=True, 
            headless=False,
            chromium_arg="user-data-dir=/home/sonu/.config/chromium,profile-directory=Profile 3") as sb:
        url = "https://www.linkedin.com/feed/update/urn:li:activity:7355286893422358528/"
        
        print("Opening LinkedIn post...")
        sb.open(url)
        sb.sleep(5)
        
        # Try to expand comments section
        print("Expanding comments section...")
        try:
            comment_selectors = [
                "//button[contains(@aria-label, 'comment')]",
                "//button[contains(text(), 'comment')]",
                "//*[contains(@class, 'social-details-social-counts__comments')]",
                "//span[contains(text(), 'comments')]"
            ]
            
            for selector in comment_selectors:
                try:
                    if sb.is_element_visible(selector):
                        sb.click(selector)
                        print("  ✓ Clicked to expand comments")
                        sb.sleep(3)
                        break
                except:
                    pass
        except:
            pass
        
        print("\nLoading all comments...")
        print("This may take several minutes...\n")
        
        previous_count = 0
        no_change_count = 0
        max_iterations = 400
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Scroll down
            sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            sb.sleep(1.5)
            
            # Try to click "Load more" or "Show more" buttons
            clicked = False
            
            button_patterns = [
                "load more comments",
                "show more comments",
                "view more comments",
                "previous comments",
                "show previous comments"
            ]
            
            for pattern in button_patterns:
                if clicked:
                    break
                try:
                    # Case-insensitive XPath search
                    xpath = f'//*[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "{pattern}")]'
                    
                    if sb.is_element_visible(xpath):
                        sb.click(xpath)
                        clicked = True
                        sb.sleep(2)
                        if iteration % 10 == 0:
                            print(f"  [Iteration {iteration}] Clicked '{pattern}' button")
                        break
                except:
                    pass
            
            # Count comments
            try:
                comment_selectors = [
                    '//div[contains(@class, "comments-comment-item")]',
                    '//article[contains(@data-urn, "comment")]',
                    '//li[contains(@class, "comments-comment-item")]',
                    '//*[contains(@class, "comment-item")]'
                ]
                
                current_count = 0
                for selector in comment_selectors:
                    try:
                        elements = sb.find_elements(selector)
                        if len(elements) > current_count:
                            current_count = len(elements)
                    except:
                        pass
                
                # Progress tracking
                if current_count > previous_count:
                    if current_count % 50 == 0 or iteration % 20 == 0:
                        print(f"  [Iteration {iteration}] Loaded {current_count} comments so far...")
                    previous_count = current_count
                    no_change_count = 0
                else:
                    no_change_count += 1
                
                # Stop if stuck
                if no_change_count >= 10 and not clicked:
                    print(f"\n  ✓ No more comments to load. Final count: {current_count} comments")
                    break
            except Exception as e:
                print(f"  Error: {e}")
                pass
            
            # Vary scrolling pattern
            if iteration % 5 == 0:
                sb.execute_script("window.scrollBy(0, -300);")
                sb.sleep(0.3)
                sb.execute_script("window.scrollBy(0, 600);")
                sb.sleep(0.3)
        
        # Extract links
        print("\nExtracting links from page source...")
        
        links = []
        
        # 1. Extract from anchor tags
        try:
            elements = sb.find_elements("a")
            for element in elements:
                try:
                    href = element.get_attribute("href")
                    if href and href.startswith("http"):
                        links.append(href)
                except:
                    pass
        except Exception as e:
            print(f"Error extracting anchor tags: {e}")

        # 2. Extract from text content using regex (for non-clickable links)
        page_source = sb.get_page_source()
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        text_links = re.findall(url_pattern, page_source)
        links.extend(text_links)
        
        # Remove duplicates and sort
        unique_links = sorted(list(set(links)))
        
        # Filter out some common internal LinkedIn assets if needed, but keeping most for now
        # Optional: Filter out empty or very short links
        filtered_links = [l for l in unique_links if len(l) > 10]
        
        print(f"\nFound {len(filtered_links)} unique links:\n")
        for i, link in enumerate(filtered_links, 1):
            print(f"{i:3d}. {link}")
        
        # Save to files
        link_data = [{"index": i, "link": link} for i, link in enumerate(filtered_links, 1)]
        
        # TXT
        with open('linkedin_links.txt', 'w') as f:
            for link in filtered_links:
                f.write(link + '\n')
        
        # JSON
        with open('linkedin_links.json', 'w') as f:
            json.dump(link_data, f, indent=2)
        
        # CSV
        with open('linkedin_links.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['index', 'link'])
            writer.writeheader()
            writer.writerows(link_data)
        
        print(f"\n{'='*60}")
        print("✓ Links saved to:")
        print("  - linkedin_links.txt")
        print("  - linkedin_links.json")
        print("  - linkedin_links.csv")
        print(f"{'='*60}")

if __name__ == "__main__":
    extract_linkedin_links()
