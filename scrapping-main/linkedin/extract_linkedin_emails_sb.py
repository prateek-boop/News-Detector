from seleniumbase import SB
import time
import re
import json
import csv

def extract_linkedin_emails():
    # SeleniumBase with UC mode and existing Chrome profile - PROPER WAY
    with SB(uc=True, 
            headless=False,
            chromium_arg="user-data-dir=/home/sonu/.config/chromium,profile-directory=Profile 3") as sb:
        url = "https://www.linkedin.com/posts/sde-jobs-and-internships_referral-alert-batch-202320242025-activity-7391139255512850432-jlG-"
        
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
        
        print("\nLoading all comments (targeting 554 comments)...")
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
                
                # Success!
                if current_count >= 554:
                    print(f"\n  ✓ SUCCESS! Loaded {current_count} comments")
                    break
                
                # Stop if stuck
                if no_change_count >= 10 and not clicked:
                    print(f"\n  ✓ No more comments to load. Final count: {current_count} comments")
                    if current_count < 554:
                        print(f"  ⚠ Note: Expected 554 but loaded {current_count}")
                        print(f"     LinkedIn may be limiting visible comments")
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
        
        # Extract emails
        print("\nExtracting emails from page source...")
        page_source = sb.get_page_source()
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, page_source)
        
        # Remove duplicates and filter
        unique_emails = sorted(list(set(emails)))
        
        # Filter out common non-user emails
        filtered_emails = [
            email for email in unique_emails 
            if not any(x in email.lower() for x in ['noreply', 'support', 'admin', 'info@linkedin'])
        ]
        
        print(f"\nFound {len(filtered_emails)} unique emails:\n")
        for i, email in enumerate(filtered_emails, 1):
            print(f"{i:3d}. {email}")
        
        # Save to files
        email_data = [{"index": i, "email": email} for i, email in enumerate(filtered_emails, 1)]
        
        # TXT
        with open('linkedin_emails.txt', 'w') as f:
            for email in filtered_emails:
                f.write(email + '\n')
        
        # JSON
        with open('linkedin_emails.json', 'w') as f:
            json.dump(email_data, f, indent=2)
        
        # CSV
        with open('linkedin_emails.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['index', 'email'])
            writer.writeheader()
            writer.writerows(email_data)
        
        print(f"\n{'='*60}")
        print("✓ Emails saved to:")
        print("  - linkedin_emails.txt")
        print("  - linkedin_emails.json")
        print("  - linkedin_emails.csv")
        print(f"{'='*60}")

if __name__ == "__main__":
    extract_linkedin_emails()
