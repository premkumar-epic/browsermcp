"""
browsemcp - Fast browser automation as a Gemini CLI extension
Uses accessibility tree (fast) + optional screenshot (vision fallback)
"""

from fastmcp import FastMCP
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import base64
import json
import os
import sys

# Add root to sys.path to allow importing flows
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flows.amazon_search import amazon_search
from flows.github_trending import github_trending
from flows.google_search import google_search
from flows.fill_form import fill_form
from flows.recorder import FlowRecorder
from flows.player import play_flow

mcp = FastMCP(
    name="browsemcp",
    instructions="""
You are a browser automation agent with access to a real web browser.

STRATEGY — always try in this order:
1. Use `browser_snapshot` first — it returns the accessibility tree (fast, no vision needed)
2. Use `browser_screenshot` only when the page is visual/canvas-heavy or snapshot isn't enough
3. Prefer `browser_click_text` over coordinates — more reliable
4. For forms: `browser_type` then `browser_key("Enter")` to submit
5. After navigation, always call `browser_snapshot` to understand the new page state
6. Call `browser_close` when the task is fully done

SPEED TIPS:
- Don't screenshot unless needed — snapshot is 10x cheaper
- Combine navigate + snapshot in one turn when possible
- If a selector fails, fall back to click_text with visible button label
""",
)

# ── Shared browser state ────────────────────────────────────────────────────

_pw = None
_browser = None
_page = None


def _get_page():
    global _pw, _browser, _page
    if _page is None or _page.is_closed():
        if _pw is None:
            _pw = sync_playwright().start()
        if _browser is None or not _browser.is_connected():
            _browser = _pw.chromium.launch(
                headless=os.getenv("BROWSEMCP_HEADLESS", "false").lower() == "true",
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
        ctx = _browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        _page = ctx.new_page()
        # Block heavy resources to speed up page loads
        _page.route(
            "**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2,ttf,eot}",
            lambda route: route.abort()
            if os.getenv("BROWSEMCP_BLOCK_MEDIA", "false").lower() == "true"
            else route.continue_(),
        )
    return _page


def _page_meta() -> dict:
    p = _get_page()
    return {"url": p.url, "title": p.title()}


# ── Tools ───────────────────────────────────────────────────────────────────


@mcp.tool
def browser_navigate(url: str) -> str:
    """Navigate to a URL. Automatically waits for the page to load."""
    page = _get_page()
    if not url.startswith("http"):
        url = "https://" + url
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(600)
    except PWTimeout:
        pass  # page may have loaded enough
    m = _page_meta()
    return f"Navigated → {m['url']}\nTitle: {m['title']}"


@mcp.tool
def browser_snapshot() -> str:
    """
    PRIMARY observation tool. Returns a structured accessibility tree of the page.
    Much faster and cheaper than a screenshot. Use this first on every new page.
    """
    page = _get_page()

    # Pull interactive + landmark elements via accessibility tree
    tree = page.evaluate("""() => {
        function getRole(el) {
            return el.getAttribute('role') ||
                   el.tagName.toLowerCase();
        }
        function label(el) {
            return (
                el.getAttribute('aria-label') ||
                el.getAttribute('placeholder') ||
                el.getAttribute('title') ||
                el.innerText?.trim().slice(0, 80) ||
                el.value?.slice(0, 80) ||
                ''
            ).replace(/\\s+/g, ' ');
        }
        const TAGS = 'a,button,input,select,textarea,h1,h2,h3,[role="button"],[role="link"],[role="menuitem"],[role="tab"]';
        const nodes = [];
        document.querySelectorAll(TAGS).forEach((el, i) => {
            if (i > 80) return;
            const r = el.getBoundingClientRect();
            if (r.width === 0 && r.height === 0) return;
            nodes.push({
                idx: i,
                role: getRole(el),
                label: label(el),
                tag: el.tagName.toLowerCase(),
                id: el.id || null,
                name: el.getAttribute('name') || null,
                type: el.getAttribute('type') || null,
                href: el.href || null,
                x: Math.round(r.x + r.width / 2),
                y: Math.round(r.y + r.height / 2),
            });
        });
        return nodes;
    }""")

    m = _page_meta()
    lines = [f"URL: {m['url']}", f"Title: {m['title']}", "", "--- Interactive Elements ---"]
    for n in tree:
        parts = [f"[{n['idx']}]", n["role"].upper()]
        if n["label"]:
            parts.append(f'"{n["label"]}"')
        if n["href"] and "http" in (n["href"] or ""):
            parts.append(f"→ {n['href'][:60]}")
        if n["id"]:
            parts.append(f"#{n['id']}")
        lines.append("  " + " ".join(parts))

    return "\n".join(lines)


@mcp.tool
def browser_screenshot() -> dict:
    """
    VISUAL fallback. Returns a screenshot when accessibility tree isn't enough
    (canvas apps, image-heavy pages, CAPTCHAs, visual verification).
    More expensive — only use when snapshot is insufficient.
    """
    page = _get_page()
    img = page.screenshot(
        type="jpeg",
        quality=60,
        clip={"x": 0, "y": 0, "width": 1280, "height": 800},
    )
    m = _page_meta()
    return {
        "content": [
            {"type": "text", "text": f"URL: {m['url']}\nTitle: {m['title']}"},
            {"type": "image", "data": base64.b64encode(img).decode(), "mimeType": "image/jpeg"},
        ]
    }


@mcp.tool
def browser_click_text(text: str, exact: bool = False) -> str:
    """
    Click an element by its visible text label. Most reliable click method.
    Set exact=True only if there are multiple elements with similar text.
    Example: browser_click_text("Add to Cart")
    """
    page = _get_page()
    try:
        if exact:
            page.get_by_text(text, exact=True).first.click(timeout=5000)
        else:
            page.get_by_text(text).first.click(timeout=5000)
        page.wait_for_timeout(500)
        return f"Clicked '{text}' → now on {page.url}"
    except Exception as e:
        return f"ERROR: Could not click '{text}' — {e}\nTip: try browser_click_coordinates with x/y from snapshot"


@mcp.tool
def browser_click_selector(selector: str) -> str:
    """
    Click an element by CSS selector. Use when you have a clear ID or class.
    Example: browser_click_selector("#submit-btn") or browser_click_selector("button.primary")
    """
    page = _get_page()
    try:
        page.click(selector, timeout=5000)
        page.wait_for_timeout(500)
        return f"Clicked '{selector}' → now on {page.url}"
    except Exception as e:
        return f"ERROR: '{selector}' not found — {e}"


@mcp.tool
def browser_click_coordinates(x: int, y: int) -> str:
    """
    Click at exact pixel coordinates. Use as last resort when text/selector fails.
    Get x/y values from browser_snapshot output.
    """
    page = _get_page()
    page.mouse.click(x, y)
    page.wait_for_timeout(500)
    return f"Clicked ({x}, {y}) → now on {page.url}"


@mcp.tool
def browser_type(selector: str, text: str, clear_first: bool = True) -> str:
    """
    Type text into an input field identified by CSS selector.
    Use clear_first=True (default) to replace existing content.
    Example: browser_type("#search", "mechanical keyboards")
    """
    page = _get_page()
    try:
        if clear_first:
            page.fill(selector, text, timeout=5000)
        else:
            page.type(selector, text, timeout=5000)
        return f"Typed '{text}' into '{selector}'"
    except Exception as e:
        return f"ERROR: Could not type into '{selector}' — {e}"


@mcp.tool
def browser_type_text(label: str, text: str) -> str:
    """
    Type into an input field found by its placeholder or label text.
    Easier than finding a CSS selector.
    Example: browser_type_text("Search", "iPhone 15")
    """
    page = _get_page()
    try:
        page.get_by_placeholder(label).first.fill(text, timeout=4000)
        return f"Typed '{text}' into field with placeholder '{label}'"
    except Exception:
        try:
            page.get_by_label(label).first.fill(text, timeout=4000)
            return f"Typed '{text}' into field labelled '{label}'"
        except Exception as e:
            return f"ERROR: Could not find input '{label}' — {e}"


@mcp.tool
def browser_key(key: str) -> str:
    """
    Press a keyboard key. Common values: Enter, Escape, Tab, ArrowDown, ArrowUp, Backspace.
    Example: browser_key("Enter") to submit a search form.
    """
    page = _get_page()
    page.keyboard.press(key)
    page.wait_for_timeout(400)
    return f"Pressed {key}"


@mcp.tool
def browser_scroll(direction: str = "down", times: int = 3) -> str:
    """
    Scroll the page. direction: 'down' or 'up'. times: how many scroll steps.
    Example: browser_scroll("down", 2) to see more content.
    """
    page = _get_page()
    delta = 600 * times * (1 if direction == "down" else -1)
    page.mouse.wheel(0, delta)
    page.wait_for_timeout(400)
    return f"Scrolled {direction} × {times}"


@mcp.tool
def browser_extract_text(selector: str = "body") -> str:
    """
    Extract visible text from the page or a specific element.
    Great for reading articles, scraping data, getting search results.
    Example: browser_extract_text(".search-results") or browser_extract_text("body")
    """
    page = _get_page()
    try:
        text = page.inner_text(selector, timeout=4000)
        # Trim whitespace-heavy blocks
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return "\n".join(lines[:200])  # cap at 200 lines
    except Exception:
        return page.inner_text("body")[:3000]


@mcp.tool
def browser_wait(ms: int = 1500) -> str:
    """
    Wait for the page to settle. Use after actions that trigger loading.
    Example: browser_wait(2000) after clicking a button that loads new content.
    """
    _get_page().wait_for_timeout(ms)
    return f"Waited {ms}ms"


@mcp.tool
def browser_go_back() -> str:
    """Go back to the previous page in browser history."""
    page = _get_page()
    page.go_back(wait_until="domcontentloaded", timeout=10000)
    page.wait_for_timeout(500)
    return f"Went back → {page.url}"


@mcp.tool
def browser_current_url() -> str:
    """Return the current URL and page title. Quick check without a full snapshot."""
    m = _page_meta()
    return f"URL: {m['url']}\nTitle: {m['title']}"


@mcp.tool
def browser_close() -> str:
    """Close the browser. Call this when the task is fully complete."""
    global _pw, _browser, _page
    try:
        if _browser:
            _browser.close()
        if _pw:
            _pw.stop()
    except Exception:
        pass
    _browser = None
    _page = None
    _pw = None
    return "Browser closed."


# ── Flow Tools ──────────────────────────────────────────────────────────────


@mcp.tool
def browser_flow_amazon_search(query: str) -> str:
    """
    Search Amazon.in for the query and return top 5 results as list of {name, price, link}
    Faster than manual browsing as it uses specialized logic.
    """
    results = amazon_search(query)
    return json.dumps(results, indent=2)


@mcp.tool
def browser_flow_github_trending() -> str:
    """
    Fetch today's trending repositories from GitHub and return list of {name, description, stars, url}
    """
    results = github_trending()
    return json.dumps(results, indent=2)


@mcp.tool
def browser_flow_google_search(query: str) -> str:
    """
    Search Google and return top results as list of {title, url, snippet}
    Faster than manual browsing.
    """
    results = google_search(query)
    return json.dumps(results, indent=2)


@mcp.tool
def browser_flow_fill_form(url: str, fields: dict) -> str:
    """
    Navigate to a URL and fill form fields by label -> value.
    Example: browser_flow_fill_form("https://example.com/login", {"Email": "user@example.com", "Password": "password123"})
    """
    results = fill_form(url, fields)
    return json.dumps(results, indent=2)


# ── Recorder Tools ───────────────────────────────────────────────────────────

_recorder = None
_recorded_name = None


@mcp.tool
def browser_record_flow(name: str, url: str = "https://www.google.com") -> str:
    """
    Start recording a manual flow. A browser window will open.
    Perform your actions, then call browser_stop_recording() when done.
    The flow will be saved with the given 'name'.
    """
    global _recorder, _recorded_name
    if _recorder is not None:
        return "ERROR: A recording is already in progress. Call browser_stop_recording() first."

    _recorded_name = name
    _recorder = FlowRecorder()
    _recorder.start(url)
    return f"Recording started for flow '{name}'. A browser window has opened. Go ahead and perform the task manually, then call browser_stop_recording() in this chat when done."


@mcp.tool
def browser_stop_recording() -> str:
    """
    Stop the current recording and save it.
    """
    global _recorder, _recorded_name
    if _recorder is None:
        return "ERROR: No recording in progress."

    steps = _recorder.stop()
    path = _recorder.save(_recorded_name)
    _recorder = None
    _recorded_name = None
    return f"Recording stopped. Saved {len(steps)} steps to {path}. You can now play it back with browser_play_flow('{name}')."


@mcp.tool
def browser_play_flow(name: str) -> str:
    """
    Replay a previously recorded flow.
    Faster and more reliable for repetitive tasks as it doesn't use AI reasoning.
    """
    results = play_flow(name)
    return json.dumps(results, indent=2)


@mcp.tool
def browser_list_flows() -> str:
    """
    List all saved flows that can be played back.
    """
    path = "flows/saved"
    if not os.path.exists(path):
        return "No flows found."

    flows = [f.replace(".json", "") for f in os.listdir(path) if f.endswith(".json")]
    if not flows:
        return "No flows found."

    return "Saved Flows:\n- " + "\n- ".join(flows)
