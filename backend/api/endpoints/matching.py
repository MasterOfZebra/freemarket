"""
Unified Matching Endpoints

Orchestrates the complete matching pipeline:
1. Location-aware candidate filtering
2. Bilateral matching
3. Chain discovery
4. Notifications
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.matching.flow import MatchingEngine

router = APIRouter(prefix="/api/matching", tags=["matching"])


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/run-pipeline")
def run_full_matching_pipeline(
    user_id: int = Query(None, description="Optional: Match only this user"),
    db: Session = Depends(get_db)
):
    """
    Run complete matching pipeline:

    1. **Location Filtering**: Only match users in common cities
    2. **Bilateral Matching**: Find 2-way exchanges
    3. **Chain Discovery**: Find 3+ way exchanges
    4. **Notifications**: Alert all participants

    Returns:
    - bilateral_matches: Number of 2-way matches found
    - exchange_chains: Number of 3+ way chains found
    - Total matches created
    """

    engine = MatchingEngine(db)
    stats = engine.run_full_pipeline(user_id)

    return {
        "success": True,
        "pipeline_ran": "complete",
        "bilateral_matches": stats["bilateral_matches"],
        "exchange_chains": stats["exchange_chains"],
        "total_matches": stats["bilateral_matches"] + stats["exchange_chains"],
        "errors": stats.get("errors", [])
    }


@router.get("/status")
def get_matching_status(db: Session = Depends(get_db)):
    """Get current matching system status"""

    from backend.models import Match, ExchangeChain

    # Count active matches
    bilateral_count = db.query(Match).filter(
        Match.status.in_(["new", "notified"])
    ).count()

    chain_count = db.query(ExchangeChain).filter(
        ExchangeChain.status.in_(["proposed"])
    ).count()

    return {
        "status": "active",
        "pending_bilateral_matches": bilateral_count,
        "pending_exchange_chains": chain_count,
        "matching_engine": "unified",
        "version": "2.0"
    }


@router.post("/test-flow")
def test_matching_flow(db: Session = Depends(get_db)):
    """
    Test the complete matching flow (for debugging)

    Returns detailed information about each phase
    """

    engine = MatchingEngine(db)

    # Test with a small sample
    from backend.models import Item

    test_items = db.query(Item).filter(Item.active == True).limit(5).all()

    if not test_items:
        return {
            "error": "No active items in database",
            "suggestion": "Create some listings first"
        }

    results = []
    for item in test_items:
        candidates = engine.find_location_aware_candidates(item)
        kind_value = item.__dict__.get('kind')
        if kind_value == 2:
            kind_str = "want"
        else:
            kind_str = "have"
        results.append({
            "item_id": item.id,
            "category": item.category,
            "kind": kind_str,
            "candidates_found": len(candidates),
            "user_locations": [u[0] for u in db.query(Item.user_id).filter(Item.user_id.isnot(None)).all()]
        })

    return {
        "test_items": len(test_items),
        "results": results,
        "status": "test_complete"
    }
