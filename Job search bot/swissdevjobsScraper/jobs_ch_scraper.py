import json
import re
import time
import random
import datetime
from datetime import timezone
import requests
import pandas as pd

# --- Configuration & Filters ---

BASE_URL = "https://www.jobs.ch"
API_URL = f"{BASE_URL}/api/v1/public/search"

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
    "Consultant", "Berater", "Advisory", "Automobilfachmann", "Automobilmechatroniker"
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
PAIN_HOOK_PATTERN = re.compile(
    r'[^.!?\n]*(?:\b(?:migrate|build|scale|automate|transform|design|implement|'
    r'migrieren|aufbauen|skalieren|automatisieren|transformieren)\b)[^.!?\n]*[.!?]',
    re.IGNORECASE
)

MAX_DAYS_ACTIVE = 90
JOBS_PER_PAGE = 20

def contains_any(text, keyword_list):
    if not text:
        return False
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
        active_from_str = active_from_str.replace('Z', '+00:00')
        active_date = datetime.datetime.fromisoformat(active_from_str)
        now = datetime.datetime.now(timezone.utc)
        
        if active_date.tzinfo is None:
             active_date = active_date.replace(tzinfo=timezone.utc)
             
        delta = now - active_date
        return max(0, delta.days) 
    except Exception as e:
        print(f"Error parsing date {active_from_str}: {e}")
        return None

def fetch_jobs_page(page, term):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    # 106 seems to be the category id representing IT/Telecom software engineering jobs
    params = {
        "term": term,
        "page": page,
        "rows": JOBS_PER_PAGE
    }
    
    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to fetch page {page}: {e}")
        return None

def scrape_jobs():
    search_terms = ["Tech", "DevOps", "SRE", "System Engineer", "Cloud Engineer"]
    
    leads = []
    seen_job_ids = set()
    all_jobs_total = 0
    
    print("Starting jobs.ch Scraper via API...")
    
    for term in search_terms:
        print(f"\n--- Searching for term: '{term}' ---")
        page = 1
        max_pages = 1 # Initial dummy value
        
        while page <= max_pages:
            print(f"Fetching page {page} for '{term}'...")
            data = fetch_jobs_page(page, term)
            
            if not data:
                print("Failed to get data or rate limited. Sleeping for 30s...")
                time.sleep(30)
                continue
                
            documents = data.get("documents", [])
            max_pages = min(data.get("num_pages", 1), 30) # Limit to 30 pages per term for reasonable execution time
            total_hits = data.get("total_hits", 0)
            
            if page == 1:
                print(f"Found {total_hits} total hits across {max_pages} pages.")
                
            if not documents:
                break
                
            all_jobs_total += len(documents)
            
            for job in documents:
                job_id = job.get('job_id')
                if job_id in seen_job_ids:
                    continue
                seen_job_ids.add(job_id)
                
                title = job.get('title', '')
                company_name = job.get('company_name', '')
                job_url_slug = job.get('_links', {}).get('detail_de', {}).get('href', '')
                if not job_url_slug.startswith('http'):
                     job_url_slug = f"https://www.jobs.ch{job.get('slug', '')}"
                     
                active_from = job.get('publication_date')
                full_text = job.get('preview', '')
                
                # Preliminary Filters
                if not contains_any(title, APPROVED_ROLES) and not contains_any(full_text, APPROVED_TECH):
                    continue
                    
                if contains_any(title, ROLE_EXCLUSIONS):
                    continue
                    
                if contains_any(company_name, COMPANY_WHALES):
                    continue
                    
                days_active = calculate_days_active(active_from)
                if days_active is None or days_active > MAX_DAYS_ACTIVE:
                    continue
                    
                full_text = job.get('preview', '')
                
                if contains_any(company_name, CONSULTANCY_BAN) or contains_any(full_text, CONSULTANCY_BAN):
                    continue
                
                # 'tags' usually looks like [{'name': 'C#'}, {'name': 'SQL'}] in jobs.ch
                all_tech_tags = [t.get('name', '') if isinstance(t, dict) else str(t) for t in job.get('tags', [])]
                matched_tech = [tech for tech in APPROVED_TECH if tech.lower() in [t.lower() for t in all_tech_tags] or tech.lower() in full_text.lower() or tech.lower() in title.lower()]
                matched_tech = list(set(matched_tech))
                
                # We will be slightly more permissive here if they have an approved role
                if not matched_tech and not contains_any(title, APPROVED_ROLES):
                    continue
                    
                pain_hook = extract_pain_hook(full_text)
                
                # We format location nicely
                locations = job.get('place', [])
                location_str = ", ".join(locations) if isinstance(locations, list) else str(locations)
                
                job_url_full = job_url_slug
                if "jobs.ch" not in job_url_full:
                    job_url_full = BASE_URL + job_url_slug
                
                leads.append({
                    "Company Name": company_name,
                    "Job Title": title,
                    "Location": location_str,
                    "Matched Tech & Skills": ", ".join(matched_tech),
                    "Date Posted": active_from[:10] if active_from else "Unknown",
                    "Days Active": days_active,
                    "Direct Job URL": job_url_full,
                    "The Pain Hook": pain_hook
                })
                
                print(f"  -> SUCCESS! Lead added: {title} @ {company_name}")
                
            page += 1
            # Add a slow polite delay to avoid WAF hitting us if we page too fast
            time.sleep(random.uniform(1.5, 3.5))

    return leads, all_jobs_total

if __name__ == "__main__":
    leads_data, total_scanned = scrape_jobs()
    
    print(f"\nCompleted scraping. Scanned {total_scanned} jobs.")
    
    if leads_data:
        df = pd.DataFrame(leads_data)
        output_file = "jobs_ch_leads.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Successfully exported {len(leads_data)} qualified leads to {output_file}.")
    else:
        print("Scraping complete! No jobs matched the strict filtering criteria.")
