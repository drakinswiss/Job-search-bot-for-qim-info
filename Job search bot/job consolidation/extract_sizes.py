import pandas as pd
import requests
import re
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

def extract_company_size(html_text):
    pattern = r'(?i)(\d+[\d,.+]*\s*(?:-\s*\d+[\d,.+]*)?)\s*(?:employees|mitarbeiter|mitarbeitende|angestellte|kollegen)'
    matches = re.findall(pattern, html_text)
    if matches:
        return matches[0] + " employees"
    pattern2 = r'(?i)(?:company size|firmengrösse|unternehmensgrösse|employees)[\s:]*(\d+[\d,.+]*\s*(?:-\s*\d+[\d,.+]*)?)'
    matches2 = re.findall(pattern2, html_text)
    if matches2:
        return matches2[0] + " employees"
    return ""

def scrape_size(url):
    if not url or pd.isna(url): return ""
    try:
        res = requests.get(url, headers=HEADERS, timeout=5)
        if res.status_code == 200:
            return extract_company_size(res.text)
    except:
        pass
    return ""

print("Loading german_swiss_qim_leads_verified.xlsx...")
df = pd.read_excel('german_swiss_qim_leads_verified.xlsx')

for idx, row in df.iterrows():
    if pd.isna(row.get('Company size')) or str(row.get('Company size')).strip() == '':
        job_url = row.get('Direct Job URL')
        comp_url = row.get('Website')
        
        print(f"[{idx+1}/{len(df)}] Scraping size for {row['Company Name']}...")
        size = scrape_size(job_url)
        if not size:
            size = scrape_size(comp_url)
            
        if size:
            print(f"  [+] Found: {size}")
            df.at[idx, 'Company size'] = size
        else:
            print("  [-] Not found")
        time.sleep(1)

df.to_excel('german_swiss_qim_leads_verified_final.xlsx', index=False)
print("Saved to german_swiss_qim_leads_verified_final.xlsx")
