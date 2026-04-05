"""
browsemcp health check — run this before publishing or after any major change.

Usage:
    python scripts/healthcheck.py           # full check (opens browser)
    python scripts/healthcheck.py --no-browser  # skip live browser tests

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
"""

import sys
import os
import json
import asyncio
import importlib
import argparse
import time
import traceback
from pathlib import Path

# ── Colour helpers ────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}")
def warn(msg): print(f"  {YELLOW}⚠{RESET} {msg}")
def info(msg): print(f"  {BLUE}→{RESET} {msg}")
def section(title): print(f"\n{BOLD}{'─'*50}\n  {title}\n{'─'*50}{RESET}")

# ── Result tracking ───────────────────────────────────────────────────────────

results = {"passed": 0, "failed": 0, "warned": 0}

def check(name, fn):
    try:
        fn()
        ok(name)
        results["passed"] += 1
    except AssertionError as e:
        fail(f"{name}: {e}")
        results["failed"] += 1
    except Exception as e:
        fail(f"{name}: {type(e).__name__}: {e}")
        results["failed"] += 1

# ── Root path ─────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

# ─────────────────────────────────────────────────────────────────────────────
# 1. PROJECT STRUCTURE
# ─────────────────────────────────────────────────────────────────────────────

def check_structure():
    section("1 / Project Structure")

    required_files = [
        "src/server.py",
        "flows/__init__.py",
        "flows/amazon_search.py",
        "flows/github_trending.py",
        "flows/google_search.py",
        "flows/fill_form.py",
        "flows/recorder.py",
        "flows/player.py",
        "flows/saved/.gitkeep",
        "sessions/manager.py",
        "sessions/.gitkeep",
        "tests/test_server.py",
        "tests/test_flows.py",
        "GEMINI.md",
        "README.md",
        "extension.json",
        "requirements.txt",
        "LICENSE",
        ".gitignore",
    ]

    for f in required_files:
        check(f"exists: {f}", lambda f=f: assert_file(ROOT / f))

def assert_file(path):
    assert Path(path).exists(), f"missing file: {path}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. DEPENDENCIES
# ─────────────────────────────────────────────────────────────────────────────

def check_dependencies():
    section("2 / Dependencies")

    def check_import(pkg, import_as=None):
        check(f"importable: {pkg}", lambda: importlib.import_module(import_as or pkg))

    check_import("fastmcp")
    check_import("playwright")
    check_import("playwright.sync_api")

    # requirements.txt is parseable
    def req_parseable():
        txt = (ROOT / "requirements.txt").read_text()
        assert "fastmcp" in txt, "fastmcp missing from requirements.txt"
        assert "playwright" in txt, "playwright missing from requirements.txt"
    check("requirements.txt is valid", req_parseable)

    # extension.json is valid JSON
    def ext_json():
        raw = (ROOT / "extension.json").read_text()
        data = json.loads(raw)
        assert "name" in data, "missing 'name' in extension.json"
        assert "mcpServers" in data, "missing 'mcpServers' in extension.json"
    check("extension.json is valid JSON", ext_json)


# ─────────────────────────────────────────────────────────────────────────────
# 3. SERVER — ALL TOOLS REGISTERED
# ─────────────────────────────────────────────────────────────────────────────

def check_server():
    section("3 / MCP Server — Tool Registration")

    EXPECTED_TOOLS = [
        # core browser tools
        "browser_navigate",
        "browser_snapshot",
        "browser_screenshot",
        "browser_click_text",
        "browser_click_selector",
        "browser_click_coordinates",
        "browser_type",
        "browser_type_text",
        "browser_key",
        "browser_scroll",
        "browser_extract_text",
        "browser_wait",
        "browser_go_back",
        "browser_current_url",
        "browser_close",
        # flow tools (v0.2)
        "browser_flow_amazon_search",
        "browser_flow_github_trending",
        "browser_flow_google_search",
        "browser_flow_fill_form",
        # recorder tools (v0.3)
        "browser_record_flow",
        "browser_stop_recording",
        "browser_play_flow",
        "browser_list_flows",
        # session tools (v0.4)
        "browser_save_session",
        "browser_load_session",
        "browser_list_sessions",
        "browser_delete_session",
    ]

    from server import mcp

    async def get_tools():
        return await mcp.list_tools()

    registered = [t.name for t in asyncio.run(get_tools())]
    info(f"Total tools registered: {len(registered)}")

    for tool in EXPECTED_TOOLS:
        check(f"tool registered: {tool}",
              lambda t=tool: assert_tool(t, registered))

    # Check for undocumented extras
    extras = [t for t in registered if t not in EXPECTED_TOOLS]
    if extras:
        for e in extras:
            warn(f"Extra tool (not in checklist): {e}")
            results["warned"] += 1

def assert_tool(name, registered):
    assert name in registered, f"'{name}' not registered"


# ─────────────────────────────────────────────────────────────────────────────
# 4. TOOL DOCSTRINGS — every tool must have one
# ─────────────────────────────────────────────────────────────────────────────

def check_docstrings():
    section("4 / Tool Docstrings")
    import ast

    server_src = (ROOT / "src" / "server.py").read_text()
    tree = ast.parse(server_src)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Only check @mcp.tool decorated functions
            decorated = any(
                (isinstance(d, ast.Attribute) and d.attr == "tool") or
                (isinstance(d, ast.Name) and d.id == "tool")
                for d in node.decorator_list
            )
            if decorated:
                has_doc = (
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant)
                )
                def _dc(n=node.name, h=has_doc):
                    if not h:
                        raise AssertionError(f"{n} has no docstring")
                check(f"docstring: {node.name}", _dc)


# ─────────────────────────────────────────────────────────────────────────────
# 5. FLOWS — importable and have correct function signatures
# ─────────────────────────────────────────────────────────────────────────────

def check_flows():
    section("5 / Pre-built Flows")

    flow_checks = [
        ("flows.amazon_search",  "amazon_search",   ["query"]),
        ("flows.github_trending","github_trending",  []),
        ("flows.google_search",  "google_search",   ["query"]),
        ("flows.fill_form",      "fill_form",        ["url", "fields"]),
        ("flows.recorder",       "FlowRecorder",     None),   # class
        ("flows.player",         "play_flow",        ["name"]),
    ]

    for module_path, symbol, expected_args in flow_checks:
        def _check(mp=module_path, sym=symbol, args=expected_args):
            mod = importlib.import_module(mp)
            assert hasattr(mod, sym), f"{sym} not found in {mp}"
            obj = getattr(mod, sym)
            if args is not None:
                import inspect
                sig = inspect.signature(obj)
                params = list(sig.parameters.keys())
                for a in args:
                    assert a in params, f"{sym} missing param '{a}', got {params}"
        check(f"{module_path}.{symbol}", _check)


# ─────────────────────────────────────────────────────────────────────────────
# 6. SESSION MANAGER — importable and has correct methods
# ─────────────────────────────────────────────────────────────────────────────

def check_sessions():
    section("6 / Session Manager")

    def _check():
        import sessions.manager as sm
        for func in ["save_session", "load_session", "list_sessions", "delete_session"]:
            assert hasattr(sm, func), f"sessions.manager missing function: {func}"
    check("sessions.manager has all 4 functions", _check)

    # sessions/ in .gitignore
    def _gitignore():
        gi = (ROOT / ".gitignore").read_text()
        assert "sessions/" in gi or "sessions" in gi, \
            "sessions/ not in .gitignore — LOGIN COOKIES COULD BE COMMITTED!"
    check(".gitignore protects sessions/", _gitignore)


# ─────────────────────────────────────────────────────────────────────────────
# 7. GEMINI.md — has all required sections
# ─────────────────────────────────────────────────────────────────────────────

def check_gemini_md():
    section("7 / GEMINI.md Completeness")

    content = (ROOT / "GEMINI.md").read_text()

    sections = [
        ("Decision Tree",       "Decision Tree"),
        ("Flow tools mentioned","browser_flow_"),
        ("Recorder mentioned",  "browser_record_flow"),
        ("Sessions mentioned",  "browser_save_session"),
        ("Speed rules",         "Speed rules"),
    ]

    for name, keyword in sections:
        check(f"GEMINI.md has: {name}",
              lambda k=keyword: assert_in(k, content))

def assert_in(needle, haystack):
    assert needle in haystack, f"'{needle}' not found in GEMINI.md"


# ─────────────────────────────────────────────────────────────────────────────
# 8. README.md — has key sections
# ─────────────────────────────────────────────────────────────────────────────

def check_readme():
    section("8 / README.md Completeness")

    content = (ROOT / "README.md").read_text()

    sections = [
        ("Install instructions",    "pip install"),
        ("Playwright install",       "playwright install chromium"),
        ("Extension install cmd",    "gemini extensions install"),
        ("Tool table",               "browser_navigate"),
        ("Flows documented",         "browser_flow_"),
        ("Recorder documented",      "browser_record_flow"),
        ("Sessions documented",      "browser_save_session"),
        ("Env vars documented",      "BROWSEMCP_HEADLESS"),
        ("License badge or mention", "MIT"),
    ]

    for name, keyword in sections:
        check(f"README has: {name}",
              lambda k=keyword: assert_in_readme(k, content))

def assert_in_readme(needle, haystack):
    assert needle in haystack, f"'{needle}' not found in README.md"


# ─────────────────────────────────────────────────────────────────────────────
# 9. LIVE BROWSER — basic smoke test (skippable)
# ─────────────────────────────────────────────────────────────────────────────

def check_live_browser():
    section("9 / Live Browser Smoke Test")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        warn("playwright not installed — skipping live test")
        results["warned"] += 1
        return

    def _navigate_and_snapshot():
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True,
                                         args=["--no-sandbox"])
            page = browser.new_page()
            t0 = time.time()
            page.goto("https://example.com", wait_until="domcontentloaded",
                      timeout=15000)
            elapsed = time.time() - t0

            assert "Example Domain" in page.title(), \
                f"Unexpected title: {page.title()}"

            # Accessibility snapshot
            els = page.evaluate("""() => {
                return document.querySelectorAll('a,button,h1,h2').length;
            }""")
            assert els > 0, "No interactive elements found on example.com"

            info(f"Page loaded in {elapsed:.2f}s, found {els} elements")
            browser.close()

    check("navigate to example.com + snapshot", _navigate_and_snapshot)

    def _screenshot():
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True,
                                         args=["--no-sandbox"])
            page = browser.new_page()
            page.goto("https://example.com", wait_until="domcontentloaded",
                      timeout=15000)
            img = page.screenshot(type="jpeg", quality=60)
            assert len(img) > 1000, "Screenshot too small — likely blank"
            info(f"Screenshot size: {len(img) // 1024}KB")
            browser.close()

    check("screenshot returns valid JPEG", _screenshot)


# ─────────────────────────────────────────────────────────────────────────────
# 10. SECURITY CHECKS
# ─────────────────────────────────────────────────────────────────────────────

def check_security():
    section("10 / Security")

    # No hardcoded API keys
    def _no_api_keys():
        bad_patterns = ["sk" + "-", "AIza", "api_key =", "api_key=", "SECRET"]
        for pyfile in ROOT.rglob("*.py"):
            # Skip virtual environments and healthcheck itself
            if ".git" in str(pyfile) or ".venv" in str(pyfile) or "venv" in str(pyfile) or pyfile.name == "healthcheck.py":
                continue
            content = pyfile.read_text(errors="ignore")
            for pat in bad_patterns:
                assert pat not in content, \
                    f"Possible hardcoded secret '{pat}' in {pyfile.name}"
    check("no hardcoded API keys in .py files", _no_api_keys)

    # sessions/ gitignored
    def _sessions_ignored():
        gi = (ROOT / ".gitignore").read_text()
        assert "sessions" in gi, "sessions/ must be in .gitignore"
    check("sessions/ is gitignored", _sessions_ignored)

    # No saved/*.json committed (would be recorded flows with real data)
    def _no_committed_flows():
        saved = ROOT / "flows" / "saved"
        if saved.exists():
            json_files = [f for f in saved.iterdir()
                         if f.suffix == ".json" and f.name != ".gitkeep"]
            assert len(json_files) == 0, \
                f"Committed flow files found: {[f.name for f in json_files]}"
    check("no recorded flows committed to git", _no_committed_flows)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-browser", action="store_true",
                        help="Skip live browser tests (faster, no internet needed)")
    args = parser.parse_args()

    print(f"\n{BOLD}browsemcp — pre-publish health check{RESET}")
    print(f"Root: {ROOT}")

    check_structure()
    check_dependencies()
    check_server()
    check_docstrings()
    check_flows()
    check_sessions()
    check_gemini_md()
    check_readme()
    check_security()

    if not args.no_browser:
        check_live_browser()
    else:
        warn("Live browser tests skipped (--no-browser)")

    # ── Summary ───────────────────────────────────────────────────────────────
    p, f, w = results["passed"], results["failed"], results["warned"]
    total = p + f

    print(f"\n{'─'*50}")
    print(f"{BOLD}  Results: {p}/{total} passed", end="")
    if w: print(f"  {YELLOW}{w} warnings{RESET}", end="")
    print(RESET)

    if f == 0:
        print(f"\n{GREEN}{BOLD}  ✅ All checks passed — safe to publish!{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{RED}{BOLD}  ❌ {f} check(s) failed — fix before publishing.{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
