import requests

def test_apis():
    endpoints = [
        "https://www.jobs.ch/api/v1/public/search",
        "https://www.jobs.ch/api/v1/public/search/job",
        "https://www.jobs.ch/api/v1/public/job/search",
        "https://www.jobs.ch/en/api/vacancies",
        "https://www.jobs.ch/api/v1/public/seo/job-search"
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    for url in endpoints:
        print(f"Testing {url}...")
        try:
            r = requests.get(url, headers=headers, timeout=5)
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                print(f"Response: {r.text[:200]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_apis()
