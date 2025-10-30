"""
Unified Matching Engine for FreeMarket

Handles:
1. Location-aware candidate filtering
2. Bilateral (2-way) exchange matching
3. Multi-way exchange chains (3+ participants)
4. Unified scoring with location bonuses
5. Participant notifications
"""

from .flow import MatchingEngine

__all__ = ["MatchingEngine"]
