"""
Moderation service for handling user reports and automated moderation.

Processes reports, manages user sanctions, and provides admin tools.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from .database import get_db
from .models import Report, ReportStatus, ReportReason, User, ListingItem
from .notification_service import get_notification_service

logger = logging.getLogger(__name__)


class ModerationService:
    """
    Service for managing user reports and automated moderation.
    """

    def __init__(self, db: Session = None):
        self.db = db or next(get_db())

    def create_report(
        self,
        reporter_id: int,
        target_listing_id: Optional[int] = None,
        target_user_id: Optional[int] = None,
        reason: ReportReason = ReportReason.OTHER,
        description: Optional[str] = None
    ) -> Optional[Report]:
        """
        Create a new user report.

        Args:
            reporter_id: User filing the report
            target_listing_id: Listing being reported (optional)
            target_user_id: User being reported (optional)
            reason: Reason for report
            description: Additional details

        Returns:
            Created Report or None if failed
        """
        try:
            # Validate that at least one target is specified
            if not target_listing_id and not target_user_id:
                logger.warning("Report must have at least one target")
                return None

            # Prevent self-reports
            if target_user_id == reporter_id:
                logger.warning("Users cannot report themselves")
                return None

            # Check for duplicate active reports
            existing = self.db.query(Report).filter(
                and_(
                    Report.reporter_id == reporter_id,
                    Report.target_listing_id == target_listing_id,
                    Report.target_user_id == target_user_id,
                    Report.status.in_([ReportStatus.PENDING, ReportStatus.UNDER_REVIEW])
                )
            ).first()

            if existing:
                logger.warning(f"Active report already exists: {existing.id}")
                return None

            # Create report
            report = Report(
                reporter_id=reporter_id,
                target_listing_id=target_listing_id,
                target_user_id=target_user_id,
                reason=reason,
                description=description,
                status=ReportStatus.PENDING
            )

            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)

            logger.info(f"Created report {report.id} by user {reporter_id}")

            # Check for auto-moderation
            self._check_auto_moderation(report)

            return report

        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            self.db.rollback()
            return None

    def _check_auto_moderation(self, report: Report):
        """
        Check if report triggers automatic moderation actions.

        Args:
            report: Newly created report
        """
        try:
            # Count active reports for target user
            if report.target_user_id:
                active_reports = self.db.query(Report).filter(
                    and_(
                        Report.target_user_id == report.target_user_id,
                        Report.status.in_([ReportStatus.PENDING, ReportStatus.UNDER_REVIEW])
                    )
                ).count()

                # Auto-escalate if 3+ active reports
                if active_reports >= 3:
                    report.status = ReportStatus.ESCALATED
                    self.db.commit()
                    logger.warning(f"Auto-escalated report {report.id} due to {active_reports} active reports")

                    # Check for auto-ban conditions
                    if active_reports >= 5:
                        self._auto_ban_user(report.target_user_id, f"Auto-ban: {active_reports} active reports")

                    # Notify admins
                    self._notify_admins_escalation(report)

            # Check for listing auto-moderation
            if report.target_listing_id:
                listing_reports = self.db.query(Report).filter(
                    and_(
                        Report.target_listing_id == report.target_listing_id,
                        Report.status.in_([ReportStatus.PENDING, ReportStatus.UNDER_REVIEW])
                    )
                ).count()

                # Auto-hide listing if 3+ reports
                if listing_reports >= 3:
                    self._auto_hide_listing(report.target_listing_id, f"Auto-hide: {listing_reports} reports")
                    logger.warning(f"Auto-hide listing {report.target_listing_id} due to {listing_reports} reports")

        except Exception as e:
            logger.error(f"Failed to check auto-moderation: {e}")

    def _auto_ban_user(self, user_id: int, reason: str):
        """
        Automatically ban a user due to severe violations.

        Args:
            user_id: User to ban
            reason: Ban reason
        """
        try:
            success = self.ban_user(user_id, 0, reason, duration_days=7)  # 7-day ban
            if success:
                logger.warning(f"Auto-banned user {user_id}: {reason}")
            else:
                logger.error(f"Failed to auto-ban user {user_id}")
        except Exception as e:
            logger.error(f"Error in auto-ban for user {user_id}: {e}")

    def _auto_hide_listing(self, listing_id: int, reason: str):
        """
        Automatically hide a listing due to reports.

        Args:
            listing_id: Listing to hide
            reason: Hide reason
        """
        try:
            success = self.hide_listing(listing_id, 0, reason)  # Admin ID 0 for system
            if success:
                logger.warning(f"Auto-hide listing {listing_id}: {reason}")
            else:
                logger.error(f"Failed to auto-hide listing {listing_id}")
        except Exception as e:
            logger.error(f"Error in auto-hide for listing {listing_id}: {e}")

    def process_bulk_reports(self, user_id: int = None, listing_id: int = None):
        """
        Process bulk moderation actions for users/listings with many reports.

        Args:
            user_id: Process reports for specific user
            listing_id: Process reports for specific listing
        """
        try:
            if user_id:
                # Check user's report history
                user_reports = self.get_user_report_stats(user_id)
                total_reports = user_reports["total_received"]

                if total_reports >= 10:
                    # Severe case - permanent ban consideration
                    logger.warning(f"User {user_id} has {total_reports} total reports - requires manual review")
                    # Could trigger admin notification here

                elif total_reports >= 7:
                    # Moderate case - temporary ban
                    self._auto_ban_user(user_id, f"Bulk moderation: {total_reports} total reports")

            if listing_id:
                # Check listing reports
                listing_reports = self.db.query(Report).filter(
                    and_(
                        Report.target_listing_id == listing_id,
                        Report.status.in_([ReportStatus.PENDING, ReportStatus.UNDER_REVIEW, ReportStatus.RESOLVED])
                    )
                ).count()

                if listing_reports >= 5:
                    # Hide permanently problematic listings
                    self._auto_hide_listing(listing_id, f"Bulk moderation: {listing_reports} reports")

        except Exception as e:
            logger.error(f"Failed to process bulk reports: {e}")

    def get_reports(
        self,
        status_filter: Optional[List[ReportStatus]] = None,
        limit: int = 50,
        offset: int = 0,
        admin_only: bool = False
    ) -> Dict[str, Any]:
        """
        Get reports with filtering.

        Args:
            status_filter: Filter by report status
            limit: Max reports to return
            offset: Pagination offset
            admin_only: Return only escalated reports

        Returns:
            Dict with reports and metadata
        """
        try:
            query = self.db.query(Report)

            if status_filter:
                query = query.filter(Report.status.in_(status_filter))
            elif admin_only:
                # Show escalated reports for admin dashboard
                query = query.filter(Report.status == ReportStatus.ESCALATED)

            reports = query.order_by(
                desc(Report.created_at)
            ).offset(offset).limit(limit).all()

            return {
                "reports": [report.to_dict() for report in reports],
                "total": len(reports),  # Simplified - would need proper count
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Failed to get reports: {e}")
            return {"reports": [], "total": 0, "limit": limit, "offset": offset}

    def update_report_status(
        self,
        report_id: int,
        new_status: ReportStatus,
        admin_id: int,
        admin_notes: Optional[str] = None,
        resolution: Optional[str] = None
    ) -> bool:
        """
        Update report status and resolution.

        Args:
            report_id: Report ID
            new_status: New status
            admin_id: Admin user ID
            admin_notes: Admin notes
            resolution: Resolution details

        Returns:
            True if updated successfully
        """
        try:
            report = self.db.query(Report).filter(Report.id == report_id).first()
            if not report:
                return False

            report.status = new_status
            report.admin_id = admin_id
            report.admin_notes = admin_notes
            report.resolution = resolution

            if new_status in [ReportStatus.RESOLVED, ReportStatus.DISMISSED]:
                report.resolved_at = datetime.utcnow()

            self.db.commit()

            logger.info(f"Updated report {report_id} status to {new_status.value} by admin {admin_id}")

            # Notify reporter about resolution
            if new_status in [ReportStatus.RESOLVED, ReportStatus.DISMISSED]:
                self._notify_report_resolution(report)

            return True

        except Exception as e:
            logger.error(f"Failed to update report status: {e}")
            self.db.rollback()
            return False

    def _notify_admins_escalation(self, report: Report):
        """
        Notify admins about escalated report.

        Args:
            report: Escalated report
        """
        # This would integrate with notification system
        # For now, just log
        logger.warning(f"ESCALATED REPORT: {report.id} - {report.reason.value}")

    def _notify_report_resolution(self, report: Report):
        """
        Notify reporter about report resolution.

        Args:
            report: Resolved report
        """
        try:
            notification_service = get_notification_service(self.db)
            import asyncio

            # Create notification for reporter
            asyncio.create_task(
                notification_service.create_event(
                    user_id=report.reporter_id,
                    event_type=notification_service.EventType.SYSTEM_WARNING,
                    payload={
                        "message": f"Your report has been {report.status.value.lower()}",
                        "report_id": report.id,
                        "resolution": report.resolution
                    }
                )
            )

        except Exception as e:
            logger.error(f"Failed to notify report resolution: {e}")

    def get_user_report_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get user's report statistics.

        Args:
            user_id: User ID

        Returns:
            Report statistics
        """
        try:
            # Reports filed by user
            filed_stats = self.db.query(
                Report.status,
                func.count(Report.id).label('count')
            ).filter(
                Report.reporter_id == user_id
            ).group_by(Report.status).all()

            # Reports against user
            received_stats = self.db.query(
                Report.status,
                func.count(Report.id).label('count')
            ).filter(
                Report.target_user_id == user_id
            ).group_by(Report.status).all()

            return {
                "filed": {status.value: count for status, count in filed_stats},
                "received": {status.value: count for status, count in received_stats},
                "total_filed": sum(count for _, count in filed_stats),
                "total_received": sum(count for _, count in received_stats)
            }

        except Exception as e:
            logger.error(f"Failed to get user report stats: {e}")
            return {
                "filed": {},
                "received": {},
                "total_filed": 0,
                "total_received": 0
            }

    def ban_user(self, user_id: int, admin_id: int, reason: str, duration_days: Optional[int] = None) -> bool:
        """
        Ban a user account.

        Args:
            user_id: User to ban
            admin_id: Admin performing ban
            reason: Ban reason
            duration_days: Ban duration (None = permanent)

        Returns:
            True if banned successfully
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            # Set ban status (assuming we add ban fields to User model)
            # For now, just mark as inactive
            user.is_active = False

            # Log the ban
            from backend.models import UserActionLog, UserActionType
            ban_log = UserActionLog(
                user_id=user_id,
                action_type=UserActionType.BAN_ISSUED,
                target_id=admin_id,
                action_metadata={
                    "reason": reason,
                    "duration_days": duration_days,
                    "banned_by": admin_id
                }
            )
            self.db.add(ban_log)

            self.db.commit()

            logger.warning(f"User {user_id} banned by admin {admin_id}: {reason}")

            # Notify user
            notification_service = get_notification_service(self.db)
            import asyncio
            asyncio.create_task(
                notification_service.create_event(
                    user_id=user_id,
                    event_type=notification_service.EventType.BAN_ISSUED,
                    payload={
                        "reason": reason,
                        "duration_days": duration_days,
                        "banned_at": datetime.utcnow().isoformat()
                    }
                )
            )

            return True

        except Exception as e:
            logger.error(f"Failed to ban user: {e}")
            self.db.rollback()
            return False

    def hide_listing(self, listing_id: int, admin_id: int, reason: str) -> bool:
        """
        Hide/moderate a listing.

        Args:
            listing_id: Listing to hide
            admin_id: Admin performing action
            reason: Reason for hiding

        Returns:
            True if hidden successfully
        """
        try:
            listing = self.db.query(ListingItem).filter(ListingItem.id == listing_id).first()
            if not listing:
                return False

            # Mark as archived (soft delete)
            listing.is_archived = True

            # Log the action
            from backend.models import UserActionLog, UserActionType
            hide_log = UserActionLog(
                user_id=listing.listing.user_id if listing.listing else None,
                action_type=UserActionType.LISTING_UPDATE,
                target_id=listing_id,
                action_metadata={
                    "action": "hidden",
                    "reason": reason,
                    "hidden_by": admin_id
                }
            )
            self.db.add(hide_log)

            self.db.commit()

            logger.info(f"Listing {listing_id} hidden by admin {admin_id}: {reason}")

            return True

        except Exception as e:
            logger.error(f"Failed to hide listing: {e}")
            self.db.rollback()
            return False


# Global service instance
_moderation_service: Optional[ModerationService] = None


def get_moderation_service(db: Session = None) -> ModerationService:
    """Get global moderation service instance"""
    global _moderation_service
    if _moderation_service is None or db:
        _moderation_service = ModerationService(db)
    return _moderation_service
