#!/usr/bin/env python3
"""
Self-check script for Freemarket backend.
Tests basic imports and API endpoints.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_imports():
    """Test basic imports."""
    try:
        from backend.main import app
        from backend.models import Item, Match
        from backend.matching import score_pair, match_for_item
        print("✅ Imports OK")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_matching():
    """Test matching functions."""
    try:
        from backend.matching import score_pair
        # Mock items
        class MockItem:
            def __init__(self, wants, offers):
                self.wants = wants
                self.offers = offers

        item_a = MockItem(["bike"], ["clothes"])
        item_b = MockItem(["clothes"], ["bike"])
        score, _, _ = score_pair(item_a, item_b)
        print(f"✅ Matching score: {score}")
        return True
    except Exception as e:
        print(f"❌ Matching failed: {e}")
        return False

if __name__ == "__main__":
    print("Running self-check...")
    ok = test_imports() and test_matching()
    if ok:
        print("🎉 All checks passed!")
        sys.exit(0)
    else:
        print("💥 Some checks failed!")
        sys.exit(1)
