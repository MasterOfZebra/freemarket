"""
A/B Testing Module for Match Threshold Optimization
"""

from sqlalchemy.orm import Session
from .models import AbMetric, Match, Notification, User
from .database import SessionLocal
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# A/B testing configurations
AB_TEST_CONFIGS = {
    'control': {'score_threshold': 0.5, 'top_k': 5},
    'variant_a': {'score_threshold': 0.6, 'top_k': 3},  # Stricter matching
    'variant_b': {'score_threshold': 0.4, 'top_k': 7}   # Looser matching
}

def get_ab_test_config(user_id: int):
    """Get A/B test config based on user ID."""
    # Simple hash-based assignment
    config_keys = list(AB_TEST_CONFIGS.keys())
    config_index = hash(str(user_id)) % len(config_keys)
    return AB_TEST_CONFIGS[config_keys[config_index]]

def update_ab_metrics(db: Session, user_id: int):
    """Update A/B metrics for a user."""
    config_key = list(AB_TEST_CONFIGS.keys())[hash(str(user_id)) % len(AB_TEST_CONFIGS)]

    # Calculate match_accept_rate: percentage of matches that became mutual
    user_matches = db.query(Match).filter(
        (Match.item_a.in_(db.query(Match.item_a).filter(Match.item_a == Match.item_b))) |
        (Match.item_b.in_(db.query(Match.item_b).filter(Match.item_a == Match.item_b)))
    ).subquery()

    # This is simplified; in practice, need to track which matches led to mutual matches
    # For now, assume match_accept_rate based on status
    accepted_matches = db.query(Match).filter(
        Match.status.in_(['accepted_a', 'accepted_b', 'matched']),
        Match.item_a.in_(db.query(Match.item_a).filter(Match.item_a == user_id)) |
        Match.item_b.in_(db.query(Match.item_b).filter(Match.item_b == user_id))
    ).count()

    total_matches = db.query(Match).filter(
        Match.item_a.in_(db.query(Match.item_a).filter(Match.item_a == user_id)) |
        Match.item_b.in_(db.query(Match.item_b).filter(Match.item_b == user_id))
    ).count()

    match_accept_rate = accepted_matches / total_matches if total_matches > 0 else 0.0

    # Calculate conversion_rate: notifications leading to contact
    # Simplified: assume sent notifications that led to accepted matches
    sent_notifications = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.status == 'sent'
    ).count()

    converted_notifications = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.status == 'sent',
        Notification.payload['type'].astext == 'mutual_match'
    ).count()

    conversion_rate = converted_notifications / sent_notifications if sent_notifications > 0 else 0.0

    # Calculate time_to_match: average time from offer creation to first match
    user_items = db.query(Match.item_a, Match.item_b, Match.created_at).filter(
        Match.item_a.in_(db.query(Match.item_a).filter(Match.item_a == user_id)) |
        Match.item_b.in_(db.query(Match.item_b).filter(Match.item_b == user_id))
    ).all()

    if user_items:
        times = []
        for item_a, item_b, match_time in user_items:
            item_id = item_a if item_a != user_id else item_b
            item_created = db.query(Match.created_at).filter(Match.id == item_id).first()
            if item_created:
                times.append((match_time - item_created[0]).total_seconds())
        avg_time_to_match = sum(times) / len(times) if times else 0
    else:
        avg_time_to_match = 0

    # Update or create metric record
    metric = db.query(AbMetric).filter(
        AbMetric.user_id == user_id,
        AbMetric.config_key == config_key
    ).first()

    if metric:
        metric.match_accept_rate = match_accept_rate
        metric.conversion_rate = float(conversion_rate)
        metric.time_to_match = timedelta(seconds=avg_time_to_match)
        setattr(metric, "match_count", total_matches)
        setattr(metric, "updated_at", datetime.utcnow())
    else:
        metric = AbMetric(
            user_id=user_id,
            config_key=config_key,
            match_accept_rate=match_accept_rate,
            conversion_rate=conversion_rate,
            time_to_match=timedelta(seconds=avg_time_to_match),
            match_count=total_matches
        )
        db.add(metric)

    db.commit()
    logger.info(f"Updated A/B metrics for user {user_id}: accept_rate={match_accept_rate:.2f}, conversion={conversion_rate:.2f}")

def auto_adjust_thresholds():
    """Automatically adjust A/B test thresholds based on metrics."""
    db: Session = SessionLocal()
    try:
        # Calculate average metrics per config
        configs = {}
        for config_key in AB_TEST_CONFIGS.keys():
            metrics = db.query(AbMetric).filter(AbMetric.config_key == config_key).all()
            if metrics:
                avg_accept = sum(m.match_accept_rate or 0 for m in metrics) / len(metrics)
                avg_conversion = sum(m.conversion_rate or 0 for m in metrics) / len(metrics)
                configs[config_key] = {
                    'avg_accept_rate': avg_accept,
                    'avg_conversion': avg_conversion
                }

        # Find best performing config
        if configs:
            best_config = max(configs.items(), key=lambda x: x[1]['avg_accept_rate'] * 0.7 + x[1]['avg_conversion'] * 0.3)
            best_key, best_metrics = best_config

            # Adjust thresholds towards the best config
            current_threshold = AB_TEST_CONFIGS[best_key]['score_threshold']
            # Slightly adjust based on performance
            if best_metrics['avg_accept_rate'] > 0.4:  # Good acceptance
                new_threshold = min(0.8, current_threshold + 0.05)
            elif best_metrics['avg_accept_rate'] < 0.2:  # Poor acceptance
                new_threshold = max(0.3, current_threshold - 0.05)
            else:
                new_threshold = current_threshold

            AB_TEST_CONFIGS[best_key]['score_threshold'] = new_threshold
            logger.info(f"Auto-adjusted threshold for {best_key} to {new_threshold}")

    except Exception as e:
        logger.error(f"Error in auto_adjust_thresholds: {e}")
    finally:
        db.close()

# Run auto-adjustment periodically (could be called from a cron job)
def periodic_ab_update():
    """Periodic task to update A/B metrics and adjust thresholds."""
    db: Session = SessionLocal()
    try:
        # Update metrics for all users with recent activity
        recent_users = db.query(User.id).filter(
            User.last_active_at > datetime.utcnow() - timedelta(days=7)
        ).all()

        for user_id in recent_users:
            update_ab_metrics(db, user_id[0])

        # Auto-adjust thresholds
        auto_adjust_thresholds()

    except Exception as e:
        logger.error(f"Error in periodic_ab_update: {e}")
    finally:
        db.close()
