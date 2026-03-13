import requests

def get_it_category():
    url = "https://www.jobs.ch/api/v1/public/search"
    headers = {"User-Agent": "Mozilla/5.0"}
    params = {"term": "software engineer"}
    
    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        docs = r.json().get("documents", [])
        if docs:
            print("Categories for 'software engineer':")
            for doc in docs[:3]:
                print(f"Job: {doc.get('title')}")
                print(f"Categories: {doc.get('categories')}")
                
if __name__ == "__main__":
    get_it_category()
