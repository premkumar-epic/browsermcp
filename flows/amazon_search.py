from playwright.sync_api import sync_playwright
import os

def amazon_search(query: str):
    """
    Search amazon.in for the query and return top 5 results as list of {name, price, link}
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
            page.goto("https://www.amazon.in", wait_until="domcontentloaded", timeout=30000)
            
            # Type search query
            search_input = page.wait_for_selector("#twotabsearchtextbox", timeout=10000)
            search_input.fill(query)
            search_input.press("Enter")
            
            page.wait_for_selector(".s-result-item", timeout=15000)
            
            results = []
            items = page.query_selector_all('.s-result-item[data-component-type="s-search-result"]')
            
            for item in items[:5]:
                name_el = item.query_selector("h2 a span")
                price_el = item.query_selector(".a-price-whole")
                link_el = item.query_selector("h2 a")
                
                if name_el and link_el:
                    name = name_el.inner_text().strip()
                    price = price_el.inner_text().strip() if price_el else "N/A"
                    link = "https://www.amazon.in" + link_el.get_attribute("href")
                    
                    # Clean link if it contains referral stuff
                    if "/ref=" in link:
                        link = link.split("/ref=")[0]
                    
                    results.append({
                        "name": name,
                        "price": price,
                        "link": link
                    })
            
            return results
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            browser.close()
