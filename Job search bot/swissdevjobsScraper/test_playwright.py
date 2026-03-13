from playwright.sync_api import sync_playwright
import json
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Create a context with user agent to look more like a real browser
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Intercept responses to see if the API returns JSON data
        api_responses = []
        
        def handle_response(response):
            if "job" in response.url.lower() and "graphql" in response.url.lower() or "api" in response.url.lower():
                try:
                    if response.ok and "application/json" in response.headers.get("content-type", ""):
                        api_responses.append({
                            "url": response.url,
                            "status": response.status,
                            # avoid reading huge bodies if not needed, but try to read
                        })
                except Exception:
                    pass
                    
        page.on("response", handle_response)
        
        print("Navigating to jobs.ch...")
        page.goto("https://www.jobs.ch/en/vacancies/?term=tech", wait_until="networkidle")
        
        print(f"Page title: {page.title()}")
        
        # Check if AWS Captcha is present
        if "captcha" in page.content().lower():
            print("WARNING: Captcha might be present on the page.")
        
        # Try to find job articles
        articles = page.locator("article").count()
        print(f"Found {articles} job articles on the page.")
        
        # See if there's any NEXT_DATA or apollo state in the page content
        content = page.content()
        if "window.__INITIAL_STATE__" in content:
            print("Found __INITIAL_STATE__")
        
        print(f"Captured {len(api_responses)} potential API responses.")
        for r in api_responses[:5]:
            print(f" - {r['url']} ({r['status']})")
            
        browser.close()

if __name__ == "__main__":
    run()
