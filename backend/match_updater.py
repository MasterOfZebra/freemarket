"""
Match Updater Worker for incremental matching.

Handles background processing of match recalculation tasks.
Uses FastAPI BackgroundTasks for simplicity (can be upgraded to Celery later).
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
import time

from .database import get_db
from .match_index_service import get_match_index_service
from .events import EventType, MatchUpdateEvent, get_event_bus
from .scoring import get_scorer, MatchingScore
from .models import User

logger = logging.getLogger(__name__)


class MatchUpdater:
    """
    Background worker for incremental match updates.

    Processes events from the event bus and recalculates matches
    only for affected users and categories.
    """

    def __init__(self, max_concurrent_tasks: int = 3):
        self.max_concurrent_tasks = max_concurrent_tasks
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self._running_tasks: Set[asyncio.Task] = set()
        self._stats = {
            "tasks_processed": 0,
            "matches_found": 0,
            "processing_time": 0.0
        }

    async def handle_match_update(self, event: MatchUpdateEvent):
        """
        Handle match update event.

        Spawns background task to recalculate matches for affected users.
        """
        async with self._semaphore:
            task = asyncio.create_task(self._process_match_update(event))
            self._running_tasks.add(task)

            try:
                await task
            except Exception as e:
                logger.error(f"Error in match update task: {e}")
            finally:
                self._running_tasks.discard(task)

    async def _process_match_update(self, event: MatchUpdateEvent):
        """
        Process single match update event.

        Args:
            event: MatchUpdateEvent with user_id and affected categories
        """
        start_time = time.time()

        try:
            logger.info(f"Processing match update for user {event.user_id}, categories: {event.categories}")

            # Get database session
            db = next(get_db())

            # Get match index service
            index_service = get_match_index_service(db)

            # Find all users who might have matches in affected categories
            all_matching_users = set()

            for category in event.categories:
                # For each category, find users who want what we offer and offer what we want
                wants_matches = index_service.find_matching_users(
                    event.user_id, [category], "want", "PERMANENT"
                )
                offers_matches = index_service.find_matching_users(
                    event.user_id, [category], "offer", "PERMANENT"
                )

                all_matching_users.update(wants_matches)
                all_matching_users.update(offers_matches)

                # Same for temporary exchanges
                temp_wants_matches = index_service.find_matching_users(
                    event.user_id, [category], "want", "TEMPORARY"
                )
                temp_offers_matches = index_service.find_matching_users(
                    event.user_id, [category], "offer", "TEMPORARY"
                )

                all_matching_users.update(temp_wants_matches)
                all_matching_users.update(temp_offers_matches)

            # Remove self from matches
            all_matching_users.discard(event.user_id)

            if not all_matching_users:
                logger.info(f"No matching users found for user {event.user_id}")
                return

            # Recalculate matches for affected users
            scorer = get_scorer()
            matches_found = 0

            for matching_user_id in all_matching_users:
                try:
                    # Check if user exists and is active
                    user = db.query(User).filter(User.id == matching_user_id).first()
                    if not user or not user.is_active:
                        continue

                    # Calculate matches (simplified - in real implementation would use full matching logic)
                    # For now, just log that we would recalculate
                    logger.debug(f"Would recalculate matches between users {event.user_id} and {matching_user_id}")

                    # TODO: Integrate with actual matching engine
                    # match_score = scorer.calculate_score(...)
                    # if match_score.is_match:
                    #     matches_found += 1

                except Exception as e:
                    logger.error(f"Error processing match for user {matching_user_id}: {e}")
                    continue

            # Update stats
            processing_time = time.time() - start_time
            self._stats["tasks_processed"] += 1
            self._stats["matches_found"] += matches_found
            self._stats["processing_time"] += processing_time

            logger.info(f"Completed match update for user {event.user_id}: "
                       f"{len(all_matching_users)} potential matches checked, "
                       f"{matches_found} matches found in {processing_time:.2f}s")

        except Exception as e:
            logger.error(f"Error processing match update for user {event.user_id}: {e}")

    def get_stats(self) -> Dict:
        """Get worker statistics"""
        return self._stats.copy()

    async def shutdown(self):
        """Gracefully shutdown worker"""
        logger.info("Shutting down MatchUpdater...")

        # Wait for running tasks to complete
        if self._running_tasks:
            await asyncio.gather(*self._running_tasks, return_exceptions=True)

        logger.info("MatchUpdater shutdown complete")


# Global worker instance
_match_updater: Optional[MatchUpdater] = None


def get_match_updater() -> MatchUpdater:
    """Get global match updater instance"""
    global _match_updater
    if _match_updater is None:
        _match_updater = MatchUpdater()
    return _match_updater


async def initialize_match_updater():
    """Initialize match updater and register event handlers"""
    updater = get_match_updater()
    event_bus = get_event_bus()

    # Register event handler
    event_bus.register_handler(EventType.MATCHES_RECALCULATED, updater.handle_match_update)

    logger.info("MatchUpdater initialized and registered with event bus")

    return updater


@asynccontextmanager
async def match_updater_lifecycle():
    """Context manager for match updater lifecycle"""
    updater = await initialize_match_updater()

    try:
        yield updater
    finally:
        await updater.shutdown()


# FastAPI Background Task wrapper for easy integration
def create_match_update_task(event: MatchUpdateEvent):
    """
    Create a background task for match updating.

    Can be used with FastAPI BackgroundTasks:
        background_tasks.add_task(create_match_update_task, event)
    """
    async def task():
        updater = get_match_updater()
        await updater.handle_match_update(event)

    return task
