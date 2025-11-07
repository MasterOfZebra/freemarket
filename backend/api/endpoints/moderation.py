"""
API endpoints for moderation and reporting system.

Provides user reporting and admin moderation tools.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.moderation_service import get_moderation_service
from backend.models import ReportReason, ReportStatus
from backend.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/moderation", tags=["moderation"])


class ReportCreateRequest(BaseModel):
    """Request model for creating a report"""
    target_listing_id: Optional[int] = None
    target_user_id: Optional[int] = None
    reason: ReportReason
    description: Optional[str] = None


class ReportUpdateRequest(BaseModel):
    """Request model for updating report status"""
    status: ReportStatus
    admin_notes: Optional[str] = None
    resolution: Optional[str] = None


@router.post("/reports")
def create_report(
    report_data: ReportCreateRequest,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Create a new user report.

    Users can report listings or other users for moderation.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Validate that at least one target is specified
    if not report_data.target_listing_id and not report_data.target_user_id:
        raise HTTPException(status_code=400, detail="Must specify target_listing_id or target_user_id")

    moderation_service = get_moderation_service(db)
    report = moderation_service.create_report(
        reporter_id=current_user.id,
        target_listing_id=report_data.target_listing_id,
        target_user_id=report_data.target_user_id,
        reason=report_data.reason,
        description=report_data.description
    )

    if not report:
        raise HTTPException(status_code=400, detail="Failed to create report or duplicate active report exists")

    return {
        "status": "created",
        "report": report.to_dict(),
        "message": "Report submitted successfully. Our moderation team will review it."
    }


@router.get("/reports")
def get_reports(
    current_user=Depends(get_current_user_optional),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Get reports (admin only or user's own reports).

    Regular users see only their filed reports.
    Admins see all reports.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    moderation_service = get_moderation_service(db)

    # Parse status filter
    status_filter = None
    if status:
        try:
            status_filter = [ReportStatus(status)]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    # Admin gets all reports, users get their own
    if current_user.is_admin:
        result = moderation_service.get_reports(
            status_filter=status_filter,
            limit=limit,
            offset=offset,
            admin_only=False
        )
    else:
        # For regular users, show only their filed reports
        result = moderation_service.get_reports(
            status_filter=status_filter,
            limit=limit,
            offset=offset
        )
        # Filter to only user's reports (simplified - would need proper query)
        result["reports"] = [
            r for r in result["reports"]
            if r["reporter_id"] == current_user.id
        ]

    return result


@router.put("/reports/{report_id}")
def update_report_status(
    report_id: int,
    update_data: ReportUpdateRequest,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Update report status (admin only).

    Allows admins to resolve or dismiss reports.
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    moderation_service = get_moderation_service(db)
    success = moderation_service.update_report_status(
        report_id=report_id,
        new_status=update_data.status,
        admin_id=current_user.id,
        admin_notes=update_data.admin_notes,
        resolution=update_data.resolution
    )

    if not success:
        raise HTTPException(status_code=404, detail="Report not found")

    return {"status": "updated", "report_id": report_id}


@router.get("/reports/{report_id}")
def get_report_details(
    report_id: int,
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get detailed report information.

    Users can see their own reports, admins see all reports.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    moderation_service = get_moderation_service(db)

    # Get reports and find the specific one
    reports_result = moderation_service.get_reports(limit=1)
    report = None

    for r in reports_result["reports"]:
        if r["id"] == report_id:
            report = r
            break

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    # Check permissions
    if not current_user.is_admin and report["reporter_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {"report": report}


@router.get("/stats")
def get_user_moderation_stats(
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get user's moderation statistics.

    Shows reports filed and reports received.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    moderation_service = get_moderation_service(db)
    stats = moderation_service.get_user_report_stats(current_user.id)

    return {
        "user_id": current_user.id,
        "stats": stats
    }


# Admin-only endpoints
@router.post("/admin/ban-user/{user_id}")
def ban_user(
    user_id: int,
    reason: str = Query(..., description="Ban reason"),
    duration_days: Optional[int] = Query(None, description="Ban duration in days"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Ban a user account (admin only).

    Args:
        user_id: User to ban
        reason: Ban reason
        duration_days: Ban duration (optional)
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    moderation_service = get_moderation_service(db)
    success = moderation_service.ban_user(
        user_id=user_id,
        admin_id=current_user.id,
        reason=reason,
        duration_days=duration_days
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to ban user or user not found")

    return {
        "status": "banned",
        "user_id": user_id,
        "reason": reason,
        "duration_days": duration_days
    }


@router.post("/admin/hide-listing/{listing_id}")
def hide_listing(
    listing_id: int,
    reason: str = Query(..., description="Reason for hiding"),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Hide/moderate a listing (admin only).

    Args:
        listing_id: Listing to hide
        reason: Reason for hiding
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    moderation_service = get_moderation_service(db)
    success = moderation_service.hide_listing(
        listing_id=listing_id,
        admin_id=current_user.id,
        reason=reason
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to hide listing or listing not found")

    return {
        "status": "hidden",
        "listing_id": listing_id,
        "reason": reason
    }


@router.get("/admin/dashboard")
def get_moderation_dashboard(
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get moderation dashboard statistics (admin only).
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from backend.models import Report, User, UserActionLog

        # Get report statistics
        report_stats = db.query(
            Report.status,
            func.count(Report.id).label('count')
        ).group_by(Report.status).all()

        # Get recent reports
        recent_reports = db.query(Report).order_by(
            desc(Report.created_at)
        ).limit(10).all()

        # Get escalated reports count
        escalated_count = db.query(Report).filter(
            Report.status == ReportStatus.ESCALATED
        ).count()

        # Get recent admin actions
        recent_actions = db.query(UserActionLog).filter(
            UserActionLog.action_type.in_(["ban_issued", "listing_update"])
        ).order_by(desc(UserActionLog.created_at)).limit(5).all()

        # Get user statistics
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        banned_users = db.query(User).filter(User.is_active == False).count()

        return {
            "report_stats": {status.value: count for status, count in report_stats},
            "recent_reports": [r.to_dict() for r in recent_reports],
            "recent_actions": [{
                "id": a.id,
                "user_id": a.user_id,
                "action": a.action_type.value,
                "target_id": a.target_id,
                "metadata": a.metadata,
                "created_at": a.created_at.isoformat() if a.created_at else None
            } for a in recent_actions],
            "escalated_count": escalated_count,
            "total_reports": sum(count for _, count in report_stats),
            "user_stats": {
                "total": total_users,
                "active": active_users,
                "banned": banned_users
            }
        }

    except Exception as e:
        logger.error(f"Failed to get moderation dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to load dashboard")


@router.get("/admin/reports/search")
def search_reports(
    q: str = Query(..., description="Search query"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Search reports with advanced filtering (admin only).
    """
    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        from backend.models import Report

        query = db.query(Report)

        # Apply search filter
        if q:
            # Search in description and reporter/target names
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    Report.description.contains(q),
                    # Would need to join with User tables for name search
                )
            )

        # Apply status filter
        if status:
            try:
                status_enum = ReportStatus(status)
                query = query.filter(Report.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        reports = query.order_by(desc(Report.created_at)).offset(offset).limit(limit).all()

        return {
            "reports": [r.to_dict() for r in reports],
            "total": total,
            "limit": limit,
            "offset": offset,
            "query": q
        }

    except Exception as e:
        logger.error(f"Failed to search reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to search reports")
