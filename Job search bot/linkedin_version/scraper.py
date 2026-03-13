import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import urllib.parse

# Define keywords based on user input
KEYWORDS = '("Performance Engineer" OR "Site Reliability Engineer" OR "SRE" OR "DevOps" OR "Performance Tester" OR "Load Tester" OR "QA Automation" OR "System Architect") AND ("Dynatrace" OR "Splunk" OR "Grafana" OR "JMeter" OR "Gatling" OR "Tricentis" OR "Tosca" OR "NeoLoad" OR "OctoPerf" OR "Datadog" OR "Prometheus" OR "OpenTelemetry" OR "AppDynamics" OR "New Relic" OR "CloudWatch" OR "Azure Monitor" OR "K6") AND NOT ("Sales" OR "Marketing" OR "Recruiter" OR "HR" OR "Financial" OR "Athlete" OR "Coach" OR "SEO")'
LOCATION = 'Switzerland'

# Known consultancy companies to filter out
CONSULTANCIES = [
    "epages", "accenture", "cognizant", "capgemini", "tcs", "tata consultancy services", 
    "wipro", "infosys", "hcl", "tech mahindra", "ibm", "deloitte", "pwc", "kpmg", "ey", 
    "ernst & young", "ti&m", "zühlke", "adesso", "ergon", "awK", "elca", "netcetera", 
    "ipt", "itera", "bystronic", "bbv", "q perior", "zuehlke"
]

def is_consultancy(company_name, description):
    name_lower = company_name.lower()
    desc_lower = description.lower()
    for consultancy in CONSULTANCIES:
        if consultancy in name_lower:
            return True
    # Sometimes consultancy name is hidden in the description "Our client, a leading bank..."
    if "our client" in desc_lower and "consulting" in desc_lower:
        return True
    return False

def extract_contact_point(text):
    # Regex to find email addresses
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    if emails:
        return ", ".join(list(set(emails)))
    return "Not Found"

def scrape_linkedin_jobs(max_jobs=100):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    }
    
    encoded_kw = urllib.parse.quote(KEYWORDS)
    # f_WT=1 corresponds to On-site
    # geoId=106693272 is Switzerland
    base_search_url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_kw}&location={LOCATION}&geoId=106693272&f_WT=1&start="
    
    jobs_data = []
    start = 0
    job_ids = set()
    consecutive_empty = 0
    
    print(f"Starting to scrape up to {max_jobs} jobs from LinkedIn...")
    
    retry_count = 0
    while len(jobs_data) < max_jobs and consecutive_empty < 3 and retry_count < 5:
        url = base_search_url + str(start)
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Failed to fetch search page, status code: {response.status_code}")
            time.sleep(5)
            retry_count += 1
            continue
            
        retry_count = 0
            
        soup = BeautifulSoup(response.text, 'html.parser')
        job_cards = soup.find_all('li')
        
        if not job_cards:
            print("No more jobs found on this page.")
            consecutive_empty += 1
            start += 10
            continue
            
        consecutive_empty = 0
        
        for card in job_cards:
            if len(jobs_data) >= max_jobs:
                break
                
            try:
                job_card_div = card.find('div', class_='base-card')
                if not job_card_div:
                    continue
                    
                job_id = job_card_div.get('data-entity-urn', '').split(':')[-1]
                
                if not job_id or job_id in job_ids:
                    continue
                    
                job_ids.add(job_id)
                
                job_title_elem = card.find('h3', class_='base-search-card__title')
                job_title = job_title_elem.text.strip() if job_title_elem else "N/A"
                
                company_elem = card.find('h4', class_='base-search-card__subtitle')
                company = company_elem.text.strip() if company_elem else "N/A"
                
                location_elem = card.find('span', class_='job-search-card__location')
                location = location_elem.text.strip() if location_elem else "N/A"
                
                date_elem = card.find('time')
                date_posted = date_elem.get('datetime', 'N/A') if date_elem else "N/A"
                
                job_url = f"https://www.linkedin.com/jobs/view/{job_id}"
                
                print(f"Fetching details for: {job_title} at {company}")
                
                # Fetch job details page
                details_response = requests.get(job_url, headers=headers)
                description = "N/A"
                contact_point = "Not Found"
                
                if details_response.status_code == 200:
                    details_soup = BeautifulSoup(details_response.text, 'html.parser')
                    desc_elem = details_soup.find('div', class_='show-more-less-html__markup')
                    
                    if desc_elem:
                        description = desc_elem.get_text(separator='\n').strip()
                        contact_point = extract_contact_point(description)
                
                # Filter consultancies
                if is_consultancy(company, description):
                    print(f"Skipping {company} as it appears to be a consultancy.")
                    continue
                
                jobs_data.append({
                    "Job Title": job_title,
                    "Company": company,
                    "Location": location,
                    "Date Posted": date_posted,
                    "Job URL": job_url,
                    "Contact Point": contact_point,
                    "Description": description
                })
                
                # Sleep to respect rate limits
                time.sleep(2)
                
            except Exception as e:
                print(f"Error parsing job card: {e}")
                
        start += 10
        time.sleep(2)
        
    print(f"Successfully scraped {len(jobs_data)} jobs.")
    
    # Save to Excel
    if jobs_data:
        df = pd.DataFrame(jobs_data)
        df.to_excel("linkedin_jobs.xlsx", index=False)
        print("Data saved to linkedin_jobs.xlsx")
    else:
        print("No jobs found matching criteria.")

if __name__ == "__main__":
    scrape_linkedin_jobs(max_jobs=100)
