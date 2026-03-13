import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urljoin, urlparse
try:
    from googlesearch import search
except ImportError:
    print("Please install googlesearch-python: pip install googlesearch-python")
    exit(1)

# Common headers to avoid 403 blocks from simple scraping scripts
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

def clean_url(url):
    url = str(url).strip()
    if pd.isna(url) or not url or url == 'nan':
        return ""
    if not url.startswith('http'):
        if '.' not in url:
            # It's a slug from swissdevjobs
            return 'https://swissdevjobs.ch/jobs/' + url
        else:
            return 'https://' + url
    return url

def verify_url(url):
    """Returns (is_valid, final_url) after following redirects or checking status."""
    url = clean_url(url)
    if not url:
        return False, ""
        
    try:
        # Some sites act up without a timeout or block bots without headers
        response = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        # We consider 200-399 valid. Sometimes 403 is "valid page but blocked bot", but we'll try to find a better one.
        if response.status_code == 200:
            return True, response.url
        elif response.status_code in [401, 403]:
            # It's an active server just blocking us, still consider the URL "existing" for Excel purposes
            return True, url
        else:
            return False, ""
    except Exception as e:
        return False, ""

def find_fallback_url(query):
    """Uses Google search to find an alternative active URL."""
    try:
        # Getting the top result
        for j in search(query, num_results=1, sleep_interval=2):
            return j
    except Exception as e:
        print(f"    [!] Search error for {query}: {e}")
        return ""
    return ""

def extract_contacts(html_text):
    """Scrapes raw text for standard Email and Swiss Phone Number regex."""
    emails = set(re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html_text))
    # Filter out png/jpg emails often found in bad scrape data
    emails = {e for e in emails if not e.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.css', '.js'))}
    
    # Swiss phones: e.g. +41 79 123 45 67, 044 123 45 67. Simple broad matching:
    phone_pattern = r'(\+41[\s.-]*\d{2}[\s.-]*\d{3}[\s.-]*\d{2}[\s.-]*\d{2}|0\d{2}[\s.-]*\d{3}[\s.-]*\d{2}[\s.-]*\d{2})'
    phones = set(re.findall(phone_pattern, html_text))
    
    return list(emails), list(phones)

def extract_company_size(html_text):
    """Attempts to find employee counts in text."""
    # Look for patterns like "100-500 employees" or "50+ Mitarbeiter"
    pattern = r'(?i)(\d+[\d,.+]*\s*(?:-\s*\d+[\d,.+]*)?)\s*(?:employees|mitarbeiter|mitarbeitende|angestellte|kollegen)'
    matches = re.findall(pattern, html_text)
    if matches:
        return matches[0] + " employees"
    # Try another pattern like "Company size: 1000"
    pattern2 = r'(?i)(?:company size|firmengrösse|unternehmensgrösse)[\s:]*(\d+[\d,.+]*\s*(?:-\s*\d+[\d,.+]*)?)'
    matches2 = re.findall(pattern2, html_text)
    if matches2:
        return matches2[0] + " employees"
    return ""

def scrape_page_for_data(url):
    """Fetches a URL and looks for contacts and size in the text."""
    if not url: return [], [], ""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            e, p = extract_contacts(response.text)
            s = extract_company_size(response.text)
            return e, p, s
    except:
        pass
    return [], [], ""

print("Loading german_swiss_qim_leads_v4.xlsx...")
input_file = 'german_swiss_qim_leads_v4.xlsx'
df = pd.read_excel(input_file)

# Initialize output lists
new_job_urls = []
new_company_urls = []
new_contacts = []
new_sizes = []

test_limit = len(df) # set to 5 for quick testing, but let's run all 79 right away with delays

for index, row in df.head(test_limit).iterrows():
    company = row['Company Name']
    job_title = row['Job Title']
    orig_job_url = row['Direct Job URL']
    orig_company_url = row['Website']
    orig_contact = str(row['Contact Point']) if not pd.isna(row['Contact Point']) else ""
    orig_size = str(row['Company size']) if not pd.isna(row['Company size']) else ""
    
    print(f"\n[{index+1}/{test_limit}] Processing: {job_title} @ {company}")
    
    # 1. Verify Job URL
    job_valid, actual_job_url = verify_url(orig_job_url)
    if job_valid:
        print(f"  [+] Job URL Valid: {actual_job_url}")
        final_job_url = actual_job_url
    else:
        print(f"  [-] Job URL Broken/Missing. Searching fallback...")
        query = f"{company} {job_title} Switzerland job"
        fallback_url = find_fallback_url(query)
        if fallback_url:
            print(f"  [+] Found fallback Job URL: {fallback_url}")
            final_job_url = fallback_url
        else:
            final_job_url = orig_job_url # Keep original if search fails
    
    # 2. Verify Company Website URL
    company_valid, actual_company_url = verify_url(orig_company_url)
    if company_valid:
        print(f"  [+] Company URL Valid: {actual_company_url}")
        final_company_url = actual_company_url
    else:
        print(f"  [-] Company URL Broken/Missing. Searching fallback...")
        query = f"{company} company Switzerland"
        fallback_url = find_fallback_url(query)
        if fallback_url:
            print(f"  [+] Found fallback Company URL: {fallback_url}")
            final_company_url = fallback_url
        else:
            final_company_url = orig_company_url
            
    # 3. Contact Details & Size
    final_contact = orig_contact if orig_contact and orig_contact.lower() not in ['nan', 'none', ''] else ""
    final_size = orig_size if orig_size and orig_size.lower() not in ['nan', 'none', ''] else ""
    
    needs_scrape = not final_contact or not final_size
    
    if needs_scrape:
        print(f"  [*] Missing data (Contact or Size). Scraping Job URL...")
        emails, phones, scraped_size = scrape_page_for_data(final_job_url)
        
        # If nothing found, try scraping Company Website (or its /contact page)
        if (not emails and not phones) or not scraped_size:
            if final_company_url:
                print(f"  [*] Attempting Company Website for missing data...")
                e2, p2, s2 = scrape_page_for_data(final_company_url)
                if not emails and not phones:
                    emails, phones = e2, p2
                if not scraped_size:
                    scraped_size = s2
            
        if not final_contact:
            if emails or phones:
                final_contact = ", ".join(emails + phones)
                print(f"  [+] Extracted new contacts: {final_contact}")
            else:
                print(f"  [-] No contacts found.")
                
        if not final_size:
            if scraped_size:
                final_size = scraped_size
                print(f"  [+] Extracted company size: {final_size}")
            else:
                print(f"  [-] No company size found.")
    else:
        print(f"  [+] Contact and Size already exist.")
            
    
    # Save the updated data
    new_job_urls.append(final_job_url)
    new_company_urls.append(final_company_url)
    new_contacts.append(final_contact)
    new_sizes.append(final_size)
    
    # Friendly delay to avoid IP blocks
    time.sleep(1.5)

print("\nSaving updated DataFrame...")
# Update the columns
test_df = df.head(test_limit).copy()
test_df['Direct Job URL'] = new_job_urls
test_df['Website'] = new_company_urls
test_df['Contact Point'] = new_contacts
test_df['Company size'] = new_sizes

test_df.to_excel('german_swiss_qim_leads_verified_v2.xlsx', index=False)
print("Saved to german_swiss_qim_leads_verified_v2.xlsx!")
