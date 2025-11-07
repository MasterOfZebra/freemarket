"""
Event system for profile changes and match updates.

Provides hooks for tracking profile modifications and triggering incremental matching.
"""
from typing import Dict, List, Optional, Any, NamedTuple
from dataclasses import dataclass
from enum import Enum
import asyncio
from contextlib import asynccontextmanager


class EventType(str, Enum):
    """Types of events in the system"""
    PROFILE_UPDATED = "profile_updated"
    MATCHES_RECALCULATED = "matches_recalculated"
    EXCHANGE_COMPLETED = "exchange_completed"


@dataclass
class ProfileChangeEvent:
    """
    Event fired when user profile (wants/offers) is modified.

    Used to trigger incremental matching updates.
    """
    user_id: int
    event_type: EventType = EventType.PROFILE_UPDATED

    # Changes in structured format
    added: Dict[str, List[Dict[str, Any]]] = None  # {"wants": [...], "offers": [...]}
    removed: Dict[str, List[Dict[str, Any]]] = None  # {"wants": [...], "offers": [...]}

    # Affected categories (computed automatically)
    affected_categories: List[str] = None

    def __post_init__(self):
        if self.added is None:
            self.added = {"wants": [], "offers": []}
        if self.removed is None:
            self.removed = {"wants": [], "offers": []}
        if self.affected_categories is None:
            self.affected_categories = self._compute_affected_categories()

    def _compute_affected_categories(self) -> List[str]:
        """Extract unique categories from added/removed items"""
        categories = set()

        for item_list in [self.added.get("wants", []), self.added.get("offers", []),
                         self.removed.get("wants", []), self.removed.get("offers", [])]:
            for item in item_list:
                if "category" in item:
                    categories.add(item["category"])

        return list(categories)

    def has_changes(self) -> bool:
        """Check if event contains actual changes"""
        return bool(self.added["wants"] or self.added["offers"] or
                   self.removed["wants"] or self.removed["offers"])


@dataclass
class MatchUpdateEvent:
    """
    Event fired when matches need recalculation for specific categories.
    """
    user_id: int
    categories: List[str]
    event_type: EventType = EventType.MATCHES_RECALCULATED

    # Optional: specific item IDs that changed
    changed_item_ids: List[int] = None

    def __post_init__(self):
        if self.changed_item_ids is None:
            self.changed_item_ids = []


class EventBus:
    """
    Simple event bus for handling profile change events.

    Supports async event handlers and background task queuing.
    """

    def __init__(self):
        self._handlers: Dict[EventType, List[callable]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()

    def register_handler(self, event_type: EventType, handler: callable):
        """Register event handler"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def publish(self, event):
        """Publish event to all registered handlers"""
        if event.__class__.__name__.endswith('Event'):
            event_type = event.event_type
        else:
            # Fallback for non-event objects
            event_type = getattr(event, 'event_type', None)

        if event_type and event_type in self._handlers:
            # Put in queue for background processing
            await self._queue.put((event_type, event))

    async def process_queue(self):
        """Process queued events (run in background task)"""
        while True:
            try:
                event_type, event = await self._queue.get()

                # Call all handlers for this event type
                for handler in self._handlers.get(event_type, []):
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(event)
                        else:
                            # Run sync handler in thread pool
                            await asyncio.get_event_loop().run_in_executor(None, handler, event)
                    except Exception as e:
                        print(f"Error in event handler {handler.__name__}: {e}")
                        # Continue processing other handlers

                self._queue.task_done()

            except Exception as e:
                print(f"Error processing event queue: {e}")
                await asyncio.sleep(1)  # Prevent tight loop on errors

    @asynccontextmanager
    async def lifecycle(self):
        """Context manager for event bus lifecycle"""
        # Start background task
        task = asyncio.create_task(self.process_queue())

        try:
            yield self
        finally:
            # Graceful shutdown
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


# Global event bus instance
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Get global event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def emit_profile_change(user_id: int, added: Dict = None, removed: Dict = None):
    """
    Emit profile change event.

    Args:
        user_id: User whose profile changed
        added: Dict with "wants" and "offers" lists of added items
        removed: Dict with "wants" and "offers" lists of removed items
    """
    event = ProfileChangeEvent(
        user_id=user_id,
        added=added or {"wants": [], "offers": []},
        removed=removed or {"wants": [], "offers": []}
    )

    if event.has_changes():
        bus = get_event_bus()
        await bus.publish(event)


async def emit_match_update(user_id: int, categories: List[str], changed_item_ids: List[int] = None):
    """
    Emit match update event for specific categories.

    Args:
        user_id: User whose matches need updating
        categories: List of affected categories
        changed_item_ids: Optional list of specific item IDs that changed
    """
    event = MatchUpdateEvent(
        user_id=user_id,
        categories=categories,
        changed_item_ids=changed_item_ids or []
    )

    bus = get_event_bus()
    await bus.publish(event)
