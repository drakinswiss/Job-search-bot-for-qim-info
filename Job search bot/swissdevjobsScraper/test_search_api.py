import requests
import json

def test_search_api():
    url = "https://www.jobs.ch/api/v1/public/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    params = {
        "term": "tech"
    }
    
    print(f"Testing {url} with params {params}...")
    r = requests.get(url, headers=headers, params=params)
    
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Total jobs: {data.get('total_hits', 'Unknown')}")
        print(f"Pages: {data.get('num_pages', 'Unknown')}")
        
        docs = data.get("documents", [])
        if docs:
            first_job = docs[0]
            print("\nFirst job data structure:")
            # Just print the keys to see what we have
            for key in first_job.keys():
                print(f" - {key}")
                
            # Print a few important ones
            print(f"\nTitle: {first_job.get('title')}")
            print(f"Company: {first_job.get('company_name')}")
            print(f"Date: {first_job.get('publication_date')}")
            print(f"Preview: {first_job.get('preview', '')[:100]}")
            
if __name__ == "__main__":
    test_search_api()
