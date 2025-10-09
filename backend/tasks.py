from sqlalchemy.orm import Session
from .database import SessionLocal, redis_client
from .models import Match, Item, User, MutualMatch
from . import matching
from .crud import create_match, create_notification
from .schemas import MatchCreate, NotificationCreate
from datetime import datetime, timedelta
import json
import logging
from typing import Any, cast, List, Awaitable

# Try to import bandit implementation; provide a safe fallback if missing
try:
    from .ml.ab_learning import BanditThreshold  # type: ignore
except Exception:
    class BanditThreshold:  # fallback minimal bandit
        def __init__(self, base_threshold: float = 0.5):
            self.threshold = base_threshold
        def get_threshold(self) -> float:
            return float(self.threshold)
        def log_reward(self, threshold: float, reward: int) -> None:
            # Naive update: slightly increase/decrease threshold based on reward
            try:
                if reward:
                    self.threshold = max(0.1, min(0.9, self.threshold - 0.01))
                else:
                    self.threshold = max(0.1, min(0.9, self.threshold + 0.01))
            except Exception:
                pass

logger = logging.getLogger(__name__)

# Initialize bandit mechanism
bandit = BanditThreshold()


# ────────────────────────────────────────────────
# Queue Management
# ────────────────────────────────────────────────

def enqueue_task(task_name: str, payload: dict) -> None:
    """Enqueue a background task."""
    task_data = {
        "task": task_name,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat()
    }
    redis_client.lpush("task_queue", json.dumps(task_data))
    logger.info(f"Enqueued task: {task_name}")


def process_task_queue() -> None:
    """Process tasks from the Redis queue."""
    while True:
        task_data = redis_client.rpop("task_queue")
        if not task_data:
            break
        # Handle awaitable or list types if necessary
        if hasattr(task_data, "__await__") and callable(getattr(task_data, "__await__")):
            import asyncio
            if isinstance(task_data, Awaitable):
                task_data = asyncio.get_event_loop().run_until_complete(task_data)
        if isinstance(task_data, list) and task_data:
            task_data = task_data[0]
        if isinstance(task_data, bytes):
            task_data = task_data.decode("utf-8")
        if not isinstance(task_data, str):
            logger.error(f"Unexpected type for task_data: {type(task_data)}")
            return
        task = json.loads(task_data)
        process_task(task)


def process_task(task: dict) -> None:
    """Process a single queued task."""
    task_name = task.get("task")
    payload = task.get("payload", {})

    db: Session = SessionLocal()
    try:
        if task_name == "cleanup_old_matches":
            cleanup_old_matches(payload.get("days_old", 30))
        elif task_name == "update_match_status":
            update_match_status(payload["match_id"], payload["status"])
        elif task_name == "find_matches":
            matching.find_matches(db, payload["user_id"])
        elif task_name == "match_for_item":
            matches = matching.match_for_item(db, payload["item_id"])
            for match in matches:
                create_match(db, MatchCreate(**match))
        elif task_name == "match_offer":
            match_offer(db, payload["offer_id"])
        else:
            logger.warning(f"Unknown task: {task_name}")
    except Exception as e:
        logger.error(f"Error processing task {task_name}: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

def cleanup_old_matches(days_old: int = 30) -> None:
    """Remove expired or rejected matches older than N days."""
    db: Session = SessionLocal()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        deleted_count = db.query(Match).filter(
            Match.created_at < cutoff_date,
            Match.status.in_(["expired", "rejected"])
        ).delete()
        db.commit()
        logger.info(f"Cleaned up {deleted_count} old matches.")
    except Exception as e:
        logger.error(f"Error cleaning matches: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


def update_match_status(match_id: int, status: str) -> None:
    """Update match status."""
    db: Session = SessionLocal()
    try:
        match = db.query(Match).filter(Match.id == match_id).first()
        if match:
            setattr(match, "status", str(status))
            db.commit()
            logger.info(f"Updated match {match_id} to status {status}")
        else:
            logger.warning(f"Match {match_id} not found")
    except Exception as e:
        logger.error(f"Error updating match status: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


# ────────────────────────────────────────────────
# Matching Logic
# ────────────────────────────────────────────────

def match_offer(db: Session, offer_id: int) -> None:
    """Match a new offer against active offers."""
    new_item = db.query(Item).filter(Item.id == offer_id).first()
    if not new_item:
        logger.warning(f"Offer {offer_id} not found")
        return

    # Try cache
    cache_key = f"active_offers:{new_item.category}"
    cached_offers = redis_client.get(cache_key)

    if cached_offers:
        if isinstance(cached_offers, bytes):
            cached_val = cached_offers.decode("utf-8")
        else:
            cached_val = str(cached_offers)
        active_offer_ids = json.loads(cached_val)
        active_offers: List[Item] = db.query(Item).filter(Item.id.in_(active_offer_ids)).all()
    else:
        active_offers = db.query(Item).filter(
            Item.active.is_(True),
            Item.user_id != new_item.user_id,
            (Item.expires_at.is_(None)) | (Item.expires_at > datetime.utcnow())
        ).all()
        redis_client.setex(cache_key, 3600, json.dumps([i.id for i in active_offers]))

    for candidate in active_offers:
        # Compute match score
        score, _, _, _ = matching.score_pair(new_item, candidate)
        dynamic_threshold = bandit.get_threshold()
        if float(score) > float(dynamic_threshold):
            # Always create a Match (if not exists)
            existing_match = db.query(Match).filter(
                ((Match.item_a == new_item.id) & (Match.item_b == candidate.id)) |
                ((Match.item_a == candidate.id) & (Match.item_b == new_item.id))
            ).first()
            if not existing_match:
                match_data = {
                    "item_a": int(getattr(new_item, "id")),
                    "item_b": int(getattr(candidate, "id")),
                    "score": float(score),
                    "reasons": {"initial_match": True},
                    "status": "new"
                }
                create_match(db, MatchCreate(**match_data))
            # Always create a MutualMatch immediately (no need to wait for reverse)
            mutual_match = MutualMatch(
                item_a=min(new_item.id, candidate.id),
                item_b=max(new_item.id, candidate.id),
            )
            db.add(mutual_match)
            db.commit()
            # Send notification for this mutual match
            send_mutual_match_notification(db, new_item, candidate, existing_match)
            reward = 1
        else:
            reward = 0
        bandit.log_reward(dynamic_threshold, reward)


# ────────────────────────────────────────────────
# Notifications
# ────────────────────────────────────────────────

def send_mutual_match_notification(db: Session, item_a: Item, item_b: Item, match: Match) -> None:
    """Send notifications for mutual match."""
    user_a = db.query(User).filter(User.id == item_a.user_id).first()
    user_b = db.query(User).filter(User.id == item_b.user_id).first()
    if not user_a or not user_b:
        return

    def build_payload(u_from: User, i_from: Item, i_partner: Item, u_partner: User, match_obj=None) -> dict[str, Any]:
        return {
            "type": "mutual_match",
            "match_id": int(getattr(match_obj, "id")) if match_obj else None,
            "partner_item": {
                "id": int(getattr(i_partner, "id")),
                "title": i_partner.title,
                "description": i_partner.description,
                "category": i_partner.category,
                "value_min": i_partner.value_min,
                "value_max": i_partner.value_max,
            },
            "partner_user": {
                "username": u_partner.username,
                "contact": u_partner.contact,
                "trust_score": u_partner.trust_score,
            },
            "message": "Найден подходящий обмен! Свяжитесь с партнером.",
        }

    # Create notifications with safe user ID extraction
    user_a_id = getattr(user_a, "id", None)
    user_b_id = getattr(user_b, "id", None)

    if user_a_id is not None and user_b_id is not None:
        create_notification(db, NotificationCreate(user_id=int(user_a_id), payload=build_payload(user_a, item_a, item_b, user_b, match)))
        create_notification(db, NotificationCreate(user_id=int(user_b_id), payload=build_payload(user_b, item_b, item_a, user_a, match)))
    else:
        logger.warning(f"Cannot send notification: user_a_id={user_a_id}, user_b_id={user_b_id}")

    logger.info(f"Sent mutual match notifications for match {match.id}")


def send_match_improvement_notification(db: Session, item_a: Item, item_b: Item, match: Match) -> None:
    """Send notification when match score improves."""
    user_a = db.query(User).filter(User.id == item_a.user_id).first()
    user_b = db.query(User).filter(User.id == item_b.user_id).first()
    if not user_a or not user_b:
        return

    def build_payload(u_from: User, i_partner: Item, u_partner: User) -> dict[str, Any]:
        return {
            "type": "match_improved",
            "match_id": int(getattr(match, "id")),
            "partner_item": {
                "id": int(getattr(i_partner, "id")),
                "title": i_partner.title,
                "description": i_partner.description,
                "category": i_partner.category,
            },
            "partner_user": {
                "username": u_partner.username,
                "trust_score": u_partner.trust_score,
            },
            "new_score": float(getattr(match, "score", 0.0) or 0.0),
            "message": f"Совпадение улучшилось! Новый скор: {float(getattr(match, 'score', 0.0) or 0.0):.2f}",
        }

    create_notification(db, NotificationCreate(user_id=int(getattr(user_a, "id")), payload=build_payload(user_a, item_b, user_b)))
    create_notification(db, NotificationCreate(user_id=int(getattr(user_b, "id")), payload=build_payload(user_b, item_a, user_a)))

    logger.info(f"Sent match improvement notifications for match {match.id}")
