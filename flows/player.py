import json
import os
import time
from playwright.sync_api import sync_playwright

def play_flow(name: str):
    """
    Replay a saved flow by name.
    """
    path = f"flows/saved/{name}.json"
    if not os.path.exists(path):
        return {"error": f"Flow '{name}' not found."}
    
    with open(path, "r") as f:
        steps = json.load(f)
    
    summary = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=os.getenv("BROWSEMCP_HEADLESS", "false").lower() == "true",
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Start by navigating to the first URL recorded
            if steps:
                first_url = steps[0].get('url', 'https://www.google.com')
                page.goto(first_url)
                summary.append(f"Started flow → {first_url}")
            
            last_url = page.url
            
            for i, step in enumerate(steps):
                action = step.get('action')
                selector = step.get('selector')
                text = step.get('text')
                url = step.get('url')
                
                # Check for navigation change
                if url and url != last_url:
                    page.goto(url)
                    last_url = url
                    summary.append(f"Navigated to {url}")
                
                try:
                    if action == 'click':
                        page.wait_for_selector(selector, timeout=5000)
                        page.click(selector)
                        summary.append(f"[{i}] Clicked {selector}")
                    
                    elif action == 'type':
                        page.wait_for_selector(selector, timeout=5000)
                        page.fill(selector, text)
                        summary.append(f"[{i}] Typed '{text}' into {selector}")
                    
                    elif action == 'scroll':
                        y = step.get('y', 0)
                        page.evaluate(f"window.scrollTo(0, {y})")
                        summary.append(f"[{i}] Scrolled to {y}")
                        
                    # Small wait between steps
                    page.wait_for_timeout(500)
                except Exception as e:
                    summary.append(f"[{i}] FAILED: {action} on {selector} — {e}")
            
            return {
                "status": "Completed",
                "flow_name": name,
                "steps_played": len(steps),
                "summary": summary
            }
            
        except Exception as e:
            return {"error": str(e), "summary": summary}
        finally:
            browser.close()
