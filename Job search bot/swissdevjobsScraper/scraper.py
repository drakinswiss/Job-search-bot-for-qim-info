import json
import re
import time
import random
import datetime
from datetime import timezone
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import pandas as pd

# --- Configuration & Filters ---

BASE_URL = "https://swissdevjobs.ch"
API_URL_LIGHT = f"{BASE_URL}/api/jobsLight"

# Approved Roles (Title must contain at least one)
APPROVED_ROLES = [
    "Performance Engineer", "Site Reliability Engineer", "SRE", "DevOps", 
    "Performance Tester", "Load Tester", "QA Automation", "System Architect", 
    "Platform Engineer", "Cloud Engineer", "System Engineer"
]

# Role Exclusions (Title must NOT contain any)
ROLE_EXCLUSIONS = [
    "Sales", "Marketing", "Recruiter", "HR", "Financial", "Athlete", 
    "Coach", "SEO", "Fullstack", "Frontend", "Backend", "Data Scientist", 
    "Consultant", "Berater", "Advisory"
]

# Consultancy Ban (Company Name or Description must NOT contain any)
CONSULTANCY_BAN = [
    "IT Services", "IT Consulting", "Digital Agency", "Hays", "Rocken", "Swisslinx"
]

# Company Whales Blocklist (Company Name must NOT contain any)
COMPANY_WHALES = [
    "Novartis", "Roche", "UBS", "Credit Suisse", "Swisscom", "SBB", "Migros", "Coop"
]

# Approved Tech Stack (Job must contain at least one)
APPROVED_TECH = [
    "Dynatrace", "Splunk", "Grafana", "JMeter", "Gatling", "Tricentis", 
    "Tosca", "NeoLoad", "OctoPerf", "Datadog", "Prometheus", "OpenTelemetry", 
    "AppDynamics", "New Relic", "CloudWatch", "Azure Monitor", "K6", 
    "Kubernetes", "Docker", "Terraform", "AWS", "Azure", "GCP", "Ansible", "CI/CD"
]

# Pain Hook Regex (English/German action verbs)
# Finds the first sentence containing one of these verbs.
PAIN_HOOK_PATTERN = re.compile(
    r'[^.!?\n]*(?:\b(?:migrate|build|scale|automate|transform|design|implement|'
    r'migrieren|aufbauen|skalieren|automatisieren|transformieren)\b)[^.!?\n]*[.!?]',
    re.IGNORECASE
)

MAX_DAYS_ACTIVE = 90

def contains_any(text, keyword_list):
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keyword_list)

def extract_pain_hook(text):
    if not text:
        return "Not Found"
    match = PAIN_HOOK_PATTERN.search(text)
    if match:
        return match.group(0).strip()
    return "Not Found"

def calculate_days_active(active_from_str):
    if not active_from_str:
        return None
    try:
        # Expected format: "2026-03-05T14:29:26.392+01:00" or similar ISO 8601
        # Replacing 'Z' with '+00:00' if present for fromisoformat compatibility in <3.11
        active_from_str = active_from_str.replace('Z', '+00:00')
        active_date = datetime.datetime.fromisoformat(active_from_str)
        now = datetime.datetime.now(timezone.utc)
        
        # In case the date doesn't have timezone info, make it UTC
        if active_date.tzinfo is None:
             active_date = active_date.replace(tzinfo=timezone.utc)
             
        delta = now - active_date
        return max(0, delta.days) # If it's a future date, return 0
    except Exception as e:
        print(f"Error parsing date {active_from_str}: {e}")
        return None

def fetch_job_details(job_url):
    """Fetches full job details by parsing the HTML of the job page."""
    full_url = urljoin(BASE_URL, f"/jobs/{job_url}")
    try:
        response = requests.get(full_url, timeout=10)
        response.raise_for_status()
        
        # The full job details are embedded in a script tag as window.__detailedJob = {...}
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tags = soup.find_all('script')
        
        for script in script_tags:
            if script.string and 'window.__detailedJob=' in script.string:
                # Extract the JSON object
                json_str = script.string.split('window.__detailedJob=')[1]
                # Semicolons might be at the end, clean it up
                if json_str.endswith(';'):
                    json_str = json_str[:-1]
                
                try:
                    data = json.loads(json_str)
                    if isinstance(data, dict):
                        return data
                    else:
                        print(f"Failed to fetch valid JSON details (got {type(data)}) for {full_url}")
                        return None
                except json.JSONDecodeError:
                    print(f"JSON decode error for {full_url}")
                    return None
        return None
    except Exception as e:
        print(f"Failed to fetch details for {full_url}: {e}")
        return None

def scrape_jobs():
    print("Fetching jobs list from API...")
    try:
        response = requests.get(API_URL_LIGHT, timeout=10)
        response.raise_for_status()
        jobs_light = response.json()
    except Exception as e:
        print(f"Failed to fetch jobs light API: {e}")
        return []

    print(f"Found {len(jobs_light)} total jobs. Starting strict filtering...")
    
    # Save all fetched jobs a separate CSV
    try:
        all_jobs_df = pd.DataFrame(jobs_light)
        all_jobs_df.to_csv("all_swissdevjobs.csv", index=False, encoding='utf-8-sig')
        print(f"Successfully exported all {len(jobs_light)} jobs to all_swissdevjobs.csv")
    except Exception as e:
        print(f"Failed to export all jobs: {e}")
        
    leads = []
    
    for i, job in enumerate(jobs_light):
        title = job.get('name', '')
        company_name = job.get('company', '')
        job_url_slug = job.get('jobUrl', '')
        active_from = job.get('activeFrom') or job.get('createdAt')
        
        # 1. Title Approval
        if not contains_any(title, APPROVED_ROLES):
            continue
            
        # 2. Title Exclusions
        if contains_any(title, ROLE_EXCLUSIONS):
            continue
            
        # 3. Company Whales Blocklist
        if contains_any(company_name, COMPANY_WHALES):
            continue
            
        # 4. Ghost Job Ban
        days_active = calculate_days_active(active_from)
        if days_active is None or days_active > MAX_DAYS_ACTIVE:
            continue
            
        # 5. Fast Tech Stack Check (using the light API array if available)
        techs_light = job.get('technologies', []) + job.get('filterTags', [])
        # Sometimes technologies aren't fully listed in light API, we might have to check full description
        
        print(f"[{i+1}/{len(jobs_light)}] Potential Match: {title} @ {company_name}")
        
        # Be polite
        time.sleep(random.uniform(1, 2))
        
        # Fetch Full Details
        detailed_job = fetch_job_details(job_url_slug)
        if not detailed_job:
            print("  -> Failed to fetch full details. Skipping.")
            continue
            
        description = detailed_job.get('description', '')
        requirements = detailed_job.get('requirementsMustTextArea', '') + " " + detailed_job.get('requirementsNiceTextArea', '')
        responsibilities = detailed_job.get('responsibilitiesTextArea', '')
        
        full_text = f"{description} {requirements} {responsibilities}"
        
        # 6. Consultancy Ban (Check Company Name & Description)
        if contains_any(company_name, CONSULTANCY_BAN) or contains_any(description, CONSULTANCY_BAN):
            print("  -> Rejected: Consultancy Ban.")
            continue
            
        # 7. Comprehensive Tech Stack Check (against full text + tags)
        all_tech_tags = detailed_job.get('technologies', []) + detailed_job.get('filterTags', [])
        matched_tech = [tech for tech in APPROVED_TECH if tech.lower() in [t.lower() for t in all_tech_tags] or tech.lower() in full_text.lower()]
        
        # De-duplicate
        matched_tech = list(set(matched_tech))
        
        if not matched_tech:
            print("  -> Rejected: No approved tech stack found.")
            continue
            
        # Extract fields
        job_url_full = urljoin(BASE_URL, f"/jobs/{job_url_slug}")
        website = detailed_job.get('companyWebsiteLink', 'Not Listed')
        if website != 'Not Listed' and not website.startswith('http'):
             website = 'https://' + website
             
        location = detailed_job.get('actualCity') or detailed_job.get('cityCategory', 'Switzerland')
        contact_email = detailed_job.get('emailAddressForApplications', 'Not Listed')
        
        # Often a specific recruiter name is not in standard fields, but could be in description
        # We will set Contact Point to email if available, else Not Listed
        contact_point = contact_email
        
        pain_hook = extract_pain_hook(full_text)
        
        leads.append({
            "Company Name": company_name,
            "Company Website": website,
            "Job Title": title,
            "Location": location,
            "Matched Tech & Skills": ", ".join(matched_tech),
            "Date Posted": detailed_job.get('createdAt', 'Unknown')[:10],
            "Days Active": days_active,
            "Contact Point": contact_point,
            "Direct Job URL": job_url_full,
            "The Pain Hook": pain_hook
        })
        
        print(f"  -> SUCCESS! Added as lead. Pain Hook: {pain_hook[:50]}...")

    return leads

if __name__ == "__main__":
    print("Starting SwissDevJobs Scraper...")
    leads_data = scrape_jobs()
    
    if leads_data:
        df = pd.DataFrame(leads_data)
        output_file = "swissdevjobs_leads.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\nScraping complete! Successfully exported {len(leads_data)} leads to {output_file}.")
    else:
        print("\nScraping complete! No jobs matched the strict filtering criteria.")
