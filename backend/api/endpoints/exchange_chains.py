"""Exchange chain endpoints for multi-way exchange matching"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import SessionLocal
from backend.schemas import NotificationCreate
from backend.crud import (
    get_exchange_chains,
    get_user_chains,
    accept_exchange_chain,
    decline_exchange_chain,
)

router = APIRouter(prefix="/api/chains", tags=["chains"])


def get_db():
    """Dependency to get DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/discover", tags=["chains"])
def discover_chains(db: Session = Depends(get_db)):
    """
    Trigger chain discovery algorithm.
    
    This endpoint runs the full exchange chain discovery pipeline:
    1. Finds unilateral matching edges
    2. Builds graph of wants → offers
    3. Detects cycles using DFS
    4. Creates ExchangeChain records
    5. Sends notifications
    
    Returns:
        Number of chains created
    """
    try:
        from backend.chain_matching import discover_and_create_chains
        
        chains_created = discover_and_create_chains(db)
        
        return {
            "success": True,
            "chains_created": chains_created,
            "message": f"Обнаружено {chains_created} новых цепочек обмена"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chain discovery failed: {str(e)}")


@router.get("/all", tags=["chains"])
def list_chains(
    status: Optional[str] = Query(None, description="Filter by status: proposed, matched, rejected"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get all exchange chains with optional filtering.
    
    Query Parameters:
        status: Filter chains by status (proposed, matched, rejected)
        skip: Number of chains to skip (pagination)
        limit: Max chains to return per page
    
    Returns:
        List of chains with metadata
    """
    
    chains, total = get_exchange_chains(db, status=status, skip=skip, limit=limit)
    
    return {
        "chains": [
            {
                "id": chain.id,
                "participants": chain.participants,
                "items": chain.items,
                "total_score": chain.total_score,
                "status": chain.status,
                "created_at": chain.created_at,
                "completed_at": chain.completed_at
            }
            for chain in chains
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/user/{user_id}", tags=["chains"])
def get_user_exchange_chains(
    user_id: int,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get all exchange chains involving a specific user.
    
    Returns:
        List of chains where user participates
    """
    
    try:
        chains = get_user_chains(db, user_id, status=status)
        
        return {
            "user_id": user_id,
            "chains": [
                {
                    "id": chain.id,
                    "participants": chain.participants,
                    "items": chain.items,
                    "total_score": chain.total_score,
                    "status": chain.status,
                    "created_at": chain.created_at,
                }
                for chain in chains
            ],
            "count": len(chains)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{chain_id}/accept", tags=["chains"])
def accept_chain(
    chain_id: int,
    user_id: int = Query(..., description="User accepting the chain"),
    db: Session = Depends(get_db)
):
    """
    User accepts their participation in exchange chain.
    
    When participant accepts, system checks if all have accepted,
    then marks chain as 'matched' and ready for execution.
    
    Returns:
        Updated chain status
    """
    
    try:
        accept_exchange_chain(db, chain_id, user_id)
        
        return {
            "success": True,
            "chain_id": chain_id,
            "user_id": user_id,
            "message": "Вы приняли участие в цепочке обмена"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{chain_id}/decline", tags=["chains"])
def decline_chain(
    chain_id: int,
    user_id: int = Query(..., description="User declining the chain"),
    db: Session = Depends(get_db)
):
    """
    User declines participation in exchange chain.
    
    Chain is marked as rejected and notifications sent to other participants.
    
    Returns:
        Confirmation of rejection
    """
    
    try:
        decline_exchange_chain(db, chain_id, user_id)
        
        return {
            "success": True,
            "chain_id": chain_id,
            "user_id": user_id,
            "message": "Вы отклонили участие в цепочке обмена"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
