from playwright.sync_api import sync_playwright
import os

def github_trending():
    """
    Fetch today's trending repos from GitHub and return list of {name, description, stars, url}
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=os.getenv("BROWSEMCP_HEADLESS", "false").lower() == "true",
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            page.goto("https://github.com/trending", wait_until="domcontentloaded", timeout=30000)
            
            page.wait_for_selector("article.Box-row", timeout=10000)
            
            repos = []
            rows = page.query_selector_all("article.Box-row")
            
            for row in rows:
                name_el = row.query_selector("h2 a")
                desc_el = row.query_selector("p.col-9")
                stars_el = row.query_selector('a[href*="/stargazers"]')
                
                if name_el:
                    name = name_el.inner_text().strip().replace("\n", "").replace(" ", "")
                    url = "https://github.com" + name_el.get_attribute("href")
                    desc = desc_el.inner_text().strip() if desc_el else "No description"
                    stars = stars_el.inner_text().strip() if stars_el else "0"
                    
                    repos.append({
                        "name": name,
                        "description": desc,
                        "stars": stars,
                        "url": url
                    })
            
            return repos
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            browser.close()
