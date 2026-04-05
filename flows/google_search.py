from playwright.sync_api import sync_playwright
import os

def google_search(query: str):
    """
    Search Google and return top results as list of {title, url, snippet}
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
            page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=30000)
            
            # Handle cookie consent if it appears
            try:
                # This depends on region, but common buttons include "Accept all" or "Agree"
                # For simplicity, we'll try to find common consent buttons
                consent_buttons = page.query_selector_all('button:has-text("Accept all"), button:has-text("I agree"), button:has-text("Agree")')
                if consent_buttons:
                    consent_buttons[0].click()
                    page.wait_for_timeout(500)
            except Exception:
                pass

            # Type search query
            search_input = page.wait_for_selector('textarea[name="q"], input[name="q"]', timeout=10000)
            search_input.fill(query)
            search_input.press("Enter")
            
            page.wait_for_selector("div#search", timeout=15000)
            
            results = []
            # 'div.g' is the container for search results
            items = page.query_selector_all('div.g')
            
            for item in items[:8]:  # Limit to 8
                title_el = item.query_selector("h3")
                link_el = item.query_selector("a")
                # Snippet is often in a div with a specific class or style
                # VwiC3b is a common snippet class
                snippet_el = item.query_selector(".VwiC3b, .yXK7lf, .MUFw9b")
                
                if title_el and link_el:
                    title = title_el.inner_text().strip()
                    url = link_el.get_attribute("href")
                    snippet = snippet_el.inner_text().strip() if snippet_el else "No snippet"
                    
                    if url and url.startswith("http"):
                        results.append({
                            "title": title,
                            "url": url,
                            "snippet": snippet
                        })
            
            return results
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            browser.close()
