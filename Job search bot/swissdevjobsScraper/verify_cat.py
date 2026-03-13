import requests

def test_cat():
    url = "https://www.jobs.ch/api/v1/public/search"
    headers = {"User-Agent": "Mozilla/5.0"}
    params = {"category-ids": 106, "rows": 5}
    
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        data = r.json()
        print(f"Total jobs in category 106: {data.get('total_hits')}")
        docs = data.get("documents", [])
        for doc in docs:
            print(f"- {doc.get('title')} @ {doc.get('company_name')}")
            
if __name__ == "__main__":
    test_cat()
