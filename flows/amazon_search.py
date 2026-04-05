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
            try:
                search_input = page.wait_for_selector("#twotabsearchtextbox", timeout=10000)
                search_input.fill(query)
                search_input.press("Enter")
            except Exception as e:
                # If home page search box fails, try direct URL
                page.goto(f"https://www.amazon.in/s?k={query.replace(' ', '+')}")

            page.wait_for_selector(".s-result-item", timeout=15000)
            
            # ALWAYS save a debug screenshot to see what's happening
            if not os.path.exists("debug"): os.makedirs("debug")
            page.screenshot(path="debug/amazon_current.png")
            # print(f"DEBUG: Page screenshotted to {os.path.abspath('debug/amazon_current.png')}")

            results = page.evaluate("""
                () => {
                    const found = [];
                    const items = document.querySelectorAll('div[data-component-type="s-search-result"], .s-result-item');
                    
                    for (const item of items) {
                        const h2 = item.querySelector('h2');
                        const link = item.querySelector('a[href*="/dp/"], a[href*="/gp/"], h2 a');
                        const price = item.querySelector('.a-price-whole');
                        
                        if (h2 && link) {
                            // If h2 is just the brand, try to find the full title nearby
                            // In many Amazon layouts, the title is a span/a near the brand
                            let name = h2.innerText.trim();
                            if (name.length < 10) {
                                const fullTitle = item.querySelector('h2 + div, h2 span, a > span');
                                if (fullTitle) name = fullTitle.innerText.trim();
                            }
                            // Fallback: just use h2 but ensure it's not empty
                            if (!name) name = h2.innerText.trim();
                            
                            if (name) {
                                found.push({
                                    name: name,
                                    price: price ? price.innerText.trim() : 'N/A',
                                    link: link.href
                                });
                            }
                        }
                        if (found.length >= 8) break;
                    }
                    return found;
                }
            """)
            
            # Clean links
            for res in results:
                if "/ref=" in res['link']:
                    res['link'] = res['link'].split("/ref=")[0]

            return results
            
        except Exception as e:
            if not os.path.exists("debug"): os.makedirs("debug")
            page.screenshot(path="debug/amazon_error.png")
            return {"error": str(e)}
        finally:
            browser.close()
