"""
Smoke test — verifies server imports and all tools are registered correctly.
Run: python tests/test_server.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    from server import mcp
    print("✓ server imports cleanly")
    return mcp

def test_tools_registered():
    mcp = test_imports()
    import asyncio
    raw = asyncio.run(mcp.list_tools())
    tools = [t.name for t in raw]
    expected = [
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
        "browser_flow_amazon_search",
        "browser_flow_github_trending",
        "browser_flow_google_search",
        "browser_flow_fill_form",
        "browser_record_flow",
        "browser_stop_recording",
        "browser_play_flow",
        "browser_list_flows",
        "browser_save_session",
        "browser_load_session",
        "browser_list_sessions",
        "browser_delete_session",
    ]
    for t in expected:
        assert t in tools, f"Missing tool: {t}"
        print(f"  ✓ {t}")
    print(f"\n✓ All {len(expected)} tools registered")

if __name__ == "__main__":
    test_tools_registered()
    print("\n✅ All checks passed")
