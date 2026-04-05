"""
Basic tests for session manager.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sessions.manager import save_session, load_session, list_sessions, delete_session

def test_session_manager_signatures():
    assert callable(save_session)
    assert callable(load_session)
    assert callable(list_sessions)
    assert callable(delete_session)
    print("✓ Session manager functions are callable")

def test_session_lifecycle():
    # Simple check of listing
    sessions = list_sessions()
    assert isinstance(sessions, list)
    print(f"✓ list_sessions returned a list: {sessions}")

if __name__ == "__main__":
    test_session_manager_signatures()
    test_session_lifecycle()
    print("\n✅ All session structure checks passed")
