#!/usr/bin/env python3
"""
Capture network requests from Devfolio to find API endpoints
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json

def capture_network_requests():
    # Enable performance logging
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print("Loading Devfolio...")
        driver.get("https://devfolio.co/hackathons/open")
        time.sleep(15)  # Wait for all requests
        
        print("\n=== NETWORK REQUESTS ===")
        logs = driver.get_log('performance')
        
        api_calls = []
        request_details = {}
        
        for log in logs:
            try:
                message = json.loads(log['message'])['message']
                
                if message['method'] == 'Network.requestWillBeSent':
                    url = message['params']['request']['url']
                    request_id = message['params']['requestId']
                    request_details[request_id] = {
                        'url': url,
                        'method': message['params']['request']['method'],
                        'headers': message['params']['request'].get('headers', {}),
                        'postData': message['params']['request'].get('postData', None)
                    }
                    
                if message['method'] == 'Network.responseReceived':
                    url = message['params']['response']['url']
                    if 'api' in url.lower() or 'graphql' in url.lower() or 'hackathon' in url.lower():
                        request_id = message['params']['requestId']
                        api_calls.append({
                            'url': url,
                            'status': message['params']['response'].get('status'),
                            'details': request_details.get(request_id, {})
                        })
            except:
                pass
        
        print("\n=== API CALLS FOUND ===")
        for call in api_calls:
            if 'devfolio.co/api' in call['url'] or 'search/hackathons' in call['url']:
                print(f"\nURL: {call['url']}")
                print(f"Status: {call.get('status')}")
                print(f"Method: {call['details'].get('method')}")
                if call['details'].get('postData'):
                    print(f"POST Data: {call['details']['postData']}")
        
        print(f"\nFound {len(api_calls)} API calls")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    capture_network_requests()
