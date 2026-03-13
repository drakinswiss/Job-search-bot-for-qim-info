import sys
from curl_cffi import requests
from bs4 import BeautifulSoup
import re

def test_curl_cffi():
    url = "https://www.jobs.ch/en/vacancies/?term=tech"
    print(f"Fetching {url} using curl_cffi...")
    
    try:
        # Impersonate a common browser
        response = requests.get(url, impersonate="chrome120")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            html = response.text
            
            # Check for AWS Captcha
            if "AWS_CAPTCHA" in html or "captcha" in html.lower():
                print("AWS Captcha is STILL present in the HTML! curl_cffi might not be enough.")
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            print(f"Title: {soup.title.text if soup.title else 'No Title'}")
            
            articles = soup.find_all("article")
            print(f"Found {len(articles)} job articles directly in HTML.")
            
            # Search for JSON payload
            match = re.search(r'window\.__INITIAL_STATE__\s*=\s*(\{.*?\});', html)
            if match:
                payload = match.group(1)
                print(f"Found __INITIAL_STATE__ payload! Length: {len(payload)} chars.")
                print(f"Preview: {payload[:200]}...")
            else:
                print("No React __INITIAL_STATE__ found.")
                
        else:
            print(f"Failed to fetch. Status code: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_curl_cffi()
