from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re
import json
import csv

# Setup Chrome with existing profile
chrome_options = Options()
chrome_options.add_argument("user-data-dir=/home/sonu/.config/chromium")
chrome_options.add_argument("profile-directory=Profile 3")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
# chrome_options.add_argument("--headless")  # Disabled headless mode for better comment loading

driver = webdriver.Chrome(options=chrome_options)

try:
    url = "https://www.linkedin.com/posts/sde-jobs-and-internships_referral-alert-batch-202320242025-activity-7391139255512850432-jlG-"
    driver.get(url)
    
    # Wait for page to load
    print("Waiting for page to load...")
    time.sleep(5)
    
    # Scroll down to ensure comments section is visible
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(2)
    
    # Click on the comments count to expand comments section
    print("Expanding comments section...")
    try:
        # Try to click comment count or "View all comments" button
        comment_triggers = [
            "//button[contains(@aria-label, 'comment')]",
            "//button[contains(text(), 'comment')]",
            "//*[contains(@class, 'social-details-social-counts__comments')]",
            "//span[contains(text(), 'comments')]/..",
            "//button[contains(@class, 'comment')]"
        ]
        
        for trigger in comment_triggers:
            try:
                elements = driver.find_elements(By.XPATH, trigger)
                for elem in elements:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                        time.sleep(1)
                        elem.click()
                        print(f"  ✓ Clicked to expand comments")
                        time.sleep(3)
                        break
                    except:
                        pass
            except:
                pass
    except Exception as e:
        print(f"  Warning: Could not click comment trigger: {e}")
    
    print("\nLoading all comments (targeting 554 comments)...")
    print("This may take several minutes...\n")
    
    previous_comment_count = 0
    no_change_count = 0
    max_iterations = 400  # Increased for 554 comments
    iteration = 0
    last_print_count = 0
    
    while iteration < max_iterations:
        iteration += 1
        
        # Scroll to bottom of comments
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        # Try to click "Load/Show more comments" or "Previous comments" buttons
        clicked_something = False
        
        button_texts = [
            "Load more comments",
            "Show more comments", 
            "View more comments",
            "Previous comments",
            "Show previous comments",
            "more comment"
        ]
        
        for text in button_texts:
            if clicked_something:
                break
            try:
                # Try with different selectors
                selectors = [
                    f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]",
                    f"//span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]/..",
                    f"//*[@role='button' and contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]"
                ]
                
                for selector in selectors:
                    try:
                        buttons = driver.find_elements(By.XPATH, selector)
                        for button in buttons:
                            try:
                                if button.is_displayed() and button.is_enabled():
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                    time.sleep(0.5)
                                    driver.execute_script("arguments[0].click();", button)  # Use JS click
                                    clicked_something = True
                                    time.sleep(1.5)
                                    if iteration % 10 == 0:
                                        print(f"  [Iteration {iteration}] Clicked '{text}' button")
                                    break
                            except:
                                pass
                        if clicked_something:
                            break
                    except:
                        pass
            except:
                pass
        
        # Count current comments
        try:
            comment_selectors = [
                "//div[contains(@class, 'comments-comment-item')]",
                "//article[contains(@data-urn, 'comment')]",
                "//li[contains(@class, 'comments-comment-item')]",
                "//*[contains(@class, 'comment-item')]"
            ]
            
            current_count = 0
            for selector in comment_selectors:
                try:
                    comments = driver.find_elements(By.XPATH, selector)
                    if len(comments) > current_count:
                        current_count = len(comments)
                except:
                    pass
            
            # Print progress every 50 comments or when we click something
            if current_count > previous_comment_count:
                if current_count - last_print_count >= 50 or iteration % 20 == 0:
                    print(f"  [Iteration {iteration}] Loaded {current_count} comments so far...")
                    last_print_count = current_count
                previous_comment_count = current_count
                no_change_count = 0
            else:
                no_change_count += 1
            
            # Success condition: reached target
            if current_count >= 554:
                print(f"\n  ✓ SUCCESS! Reached target! Loaded {current_count} comments")
                break
            
            # Stop if no progress for a while
            if no_change_count >= 10 and not clicked_something:
                print(f"\n  ✓ No more comments to load. Final count: {current_count} comments")
                if current_count < 554:
                    print(f"  ⚠ Note: Expected 554 comments but loaded {current_count}")
                    print(f"     This might be due to LinkedIn's comment visibility restrictions")
                break
            
        except Exception as e:
            print(f"  Error counting comments: {e}")
            pass
        
        # Additional scrolling patterns
        if iteration % 5 == 0:
            # Scroll up a bit then down again
            driver.execute_script("window.scrollBy(0, -500);")
            time.sleep(0.3)
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(0.3)
    
    # Get all comment elements
    print("Extracting comments...")
    page_source = driver.page_source
    
    # Extract emails using regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, page_source)
    
    # Remove duplicates and sort
    unique_emails = sorted(list(set(emails)))
    
    print(f"\nFound {len(unique_emails)} unique emails:\n")
    for email in unique_emails:
        print(email)
    
    # Prepare data for export
    email_data = [{"email": email, "index": i+1} for i, email in enumerate(unique_emails)]
    
    # Save to TXT file
    with open('linkedin_emails.txt', 'w') as f:
        for email in unique_emails:
            f.write(email + '\n')
    
    # Save to JSON file
    with open('linkedin_emails.json', 'w') as f:
        json.dump(email_data, f, indent=2)
    
    # Save to CSV file
    with open('linkedin_emails.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['index', 'email'])
        writer.writeheader()
        writer.writerows(email_data)
    
    print(f"\nEmails saved to:")
    print("  - linkedin_emails.txt")
    print("  - linkedin_emails.json")
    print("  - linkedin_emails.csv")

finally:
    driver.quit()
