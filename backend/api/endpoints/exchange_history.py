"""
API endpoints for exchange history and lifecycle tracking.

Provides user exchange history with filtering and search.
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.exchange_history_service import get_exchange_history_service
from backend.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/exchanges", tags=["exchange_history"])


@router.get("/my-exchanges")
def get_my_exchanges(
    current_user=Depends(get_current_user_optional),
    status: Optional[str] = Query(None, description="Filter by status: active, completed, cancelled"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get current user's exchange history with filtering.

    Query parameters:
    - status: Filter by exchange status (active, completed, cancelled)
    - limit: Max exchanges to return (1-100)
    - offset: Pagination offset
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if status and status not in ["active", "completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status filter")

    exchange_service = get_exchange_history_service(db)
    result = exchange_service.get_user_exchange_history(
        user_id=current_user.id,
        status_filter=status,
        limit=limit,
        offset=offset
    )

    return result


@router.get("/{exchange_id}/history")
def get_exchange_history(
    exchange_id: str,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get complete history of a specific exchange.

    User must be a participant in the exchange.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Check if user is participant (simplified check)
    exchange_service = get_exchange_history_service(db)
    participants = exchange_service._get_exchange_participants(exchange_id)

    if current_user.id not in participants:
        raise HTTPException(status_code=403, detail="Not authorized to view this exchange")

    history = exchange_service.get_exchange_history(exchange_id)

    return {
        "exchange_id": exchange_id,
        "participants": participants,
        "history": history
    }


@router.get("/{exchange_id}/status")
def get_exchange_status(
    exchange_id: str,
    db: Session = Depends(get_db)
):
    """
    Get current status of an exchange.
    """
    exchange_service = get_exchange_history_service(db)

    # Get latest event
    history = exchange_service.get_exchange_history(exchange_id)
    if not history:
        raise HTTPException(status_code=404, detail="Exchange not found")

    latest_event = max(history, key=lambda x: x['created_at'])

    # Determine status from event types
    event_types = [event['event_type'] for event in history]
    status = exchange_service._determine_exchange_status(
        [exchange_service.db.query().filter_by(event_type=et).first() for et in event_types]
    )

    return {
        "exchange_id": exchange_id,
        "status": status,
        "latest_event": latest_event,
        "participants": exchange_service._get_exchange_participants(exchange_id)
    }


# Admin endpoints
@router.get("/admin/exchange/{exchange_id}/history")
def get_exchange_history_admin(
    exchange_id: str,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Get complete history of any exchange.

    Requires admin privileges.
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    exchange_service = get_exchange_history_service(db)
    history = exchange_service.get_exchange_history(exchange_id)

    return {
        "exchange_id": exchange_id,
        "participants": exchange_service._get_exchange_participants(exchange_id),
        "history": history
    }


@router.get("/my-exchanges/export")
def export_exchange_history(
    current_user=Depends(get_current_user_optional),
    format: str = Query("json", description="Export format: json or csv"),
    db: Session = Depends(get_db)
):
    """
    Export user's exchange history.

    Query parameters:
    - format: Export format (json or csv)
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    exchange_service = get_exchange_history_service(db)
    result = exchange_service.get_user_exchange_history(
        user_id=current_user.id,
        status_filter=None,  # Export all exchanges
        limit=1000,  # Large limit for export
        offset=0
    )

    if format.lower() == "csv":
        import csv
        import io
        from fastapi.responses import StreamingResponse

        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "Exchange ID", "Status", "Other Participant", "Last Activity",
            "Event Types", "Event Count"
        ])

        # Data rows
        for exchange in result["exchanges"]:
            other_participant = exchange.get("other_participant", {})
            participant_name = other_participant.get("full_name", "Unknown") if other_participant else "Unknown"

            writer.writerow([
                exchange["exchange_id"],
                exchange["status"],
                participant_name,
                exchange.get("last_activity", ""),
                ", ".join(exchange.get("event_types", [])),
                len(exchange.get("event_types", []))
            ])

        output.seek(0)
        response = StreamingResponse(
            io.StringIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=exchange_history.csv"}
        )
        return response

    else:  # JSON format
        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=result,
            headers={"Content-Disposition": "attachment; filename=exchange_history.json"}
        )
