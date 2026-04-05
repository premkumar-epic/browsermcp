import json
import os
import time
from playwright.sync_api import sync_playwright

class FlowRecorder:
    def __init__(self):
        self.steps = []
        self._pw = None
        self._browser = None
        self._context = None
        self._page = None
        self._is_recording = False

    def _on_event(self, source, event):
        if not self._is_recording:
            return
        
        event['timestamp'] = time.time()
        # Add URL if not present or if it's a navigation
        if 'url' not in event:
            event['url'] = self._page.url
            
        print(f"Captured: {event['action']} on {event.get('selector', 'N/A')}")
        self.steps.append(event)

    def start(self, url="about:blank"):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=False, # Must be False for recording
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        self._context = self._browser.new_context()
        
        # Expose binding to receive events from JS
        self._context.expose_binding("recordEvent", self._on_event)
        
        self._page = self._context.new_page()
        self._is_recording = True
        
        # Inject recording script on every page load
        self._context.add_init_script("""
            window.addEventListener('click', (e) => {
                const selector = getSelector(e.target);
                window.recordEvent({
                    action: 'click',
                    selector: selector,
                    text: e.target.innerText?.slice(0, 50)
                });
            }, true);

            window.addEventListener('input', (e) => {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                    const selector = getSelector(e.target);
                    window.recordEvent({
                        action: 'type',
                        selector: selector,
                        text: e.target.value
                    });
                }
            }, true);

            window.addEventListener('scroll', (e) => {
                // Debounce scroll? For now just record
                window.recordEvent({
                    action: 'scroll',
                    y: window.scrollY,
                    url: window.location.href
                });
            }, true);

            function getSelector(el) {
                if (el.id) return `#${el.id}`;
                if (el === document.body) return 'body';
                let path = [];
                while (el.parentElement) {
                    let index = Array.from(el.parentElement.children).indexOf(el) + 1;
                    path.unshift(`${el.tagName.toLowerCase()}:nth-child(${index})`);
                    el = el.parentElement;
                }
                return path.join(' > ');
            }
        """)
        
        if url and url != "about:blank":
            if not url.startswith("http"):
                url = "https://" + url
            self._page.goto(url)
        else:
            self._page.goto("https://www.google.com") # Default start

    def stop(self):
        self._is_recording = False
        steps = self.steps
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()
        return steps

    def save(self, name):
        if not os.path.exists("flows/saved"):
            os.makedirs("flows/saved")
        
        path = f"flows/saved/{name}.json"
        with open(path, "w") as f:
            json.dump(self.steps, f, indent=2)
        return path
