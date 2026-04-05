"""
Basic tests for flow implementations.
Verifies imports and basic function signatures.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flows.amazon_search import amazon_search
from flows.github_trending import github_trending
from flows.google_search import google_search
from flows.fill_form import fill_form

def test_amazon_search_signature():
    assert callable(amazon_search)
    print("✓ amazon_search is callable")

def test_github_trending_signature():
    assert callable(github_trending)
    print("✓ github_trending is callable")

def test_google_search_signature():
    assert callable(google_search)
    print("✓ google_search is callable")

def test_fill_form_signature():
    assert callable(fill_form)
    print("✓ fill_form is callable")

if __name__ == "__main__":
    test_amazon_search_signature()
    test_github_trending_signature()
    test_google_search_signature()
    test_fill_form_signature()
    print("\n✅ All flow structure checks passed")
