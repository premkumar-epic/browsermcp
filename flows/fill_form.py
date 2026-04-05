from playwright.sync_api import sync_playwright
import os

def fill_form(url: str, fields: dict):
    """
    Navigate to a URL and fill form fields by label -> value.
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
            if not url.startswith("http"):
                url = "https://" + url
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            filled = []
            for label, value in fields.items():
                try:
                    # Try label first, then placeholder
                    try:
                        page.get_by_label(label).first.fill(value, timeout=5000)
                        filled.append(label)
                    except Exception:
                        page.get_by_placeholder(label).first.fill(value, timeout=5000)
                        filled.append(label)
                except Exception as e:
                    print(f"Failed to fill {label}: {e}")
            
            return {
                "status": "Success",
                "url": page.url,
                "title": page.title(),
                "filled_fields": filled
            }
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            browser.close()
