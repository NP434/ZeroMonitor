# event_bus.py
"""
Event Bus Module

Provides a centralized event distribution system for inter-module communication.
Uses a thread-safe queue to dispatch events to registered subscribers.
"""

from collections import defaultdict
from queue import Queue
import threading
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    Centralized event bus for asynchronous inter-module communication.

    Allows modules to publish events and subscribe to event types without
    direct coupling. Uses a thread-safe queue with daemon processing.
    """

    def __init__(self):
        """Initialize the event bus with subscriber registry and event queue."""
        # Dictionary mapping event types to lists of handler functions
        self.subscribers = defaultdict(list)
        # Thread-safe queue for event distribution
        self.queue = Queue()
        self.running = False

    def subscribe(self, event_type: str, handler):
        """
        Subscribe a handler function to an event type.

        Args:
            event_type: Type of event to subscribe to
            handler: Callable that will be invoked when event is published
        """
        self.subscribers[event_type].append(handler)

    def publish(self, event_type: str, data=None):
        """
        Publish an event to all subscribers.

        Args:
            event_type: Type of event being published
            data: Event payload/data (optional)
        """
        self.queue.put((event_type, data))

    def start(self):
        """Start the event processing daemon thread."""
        self.running = True
        # Daemon thread terminates when main thread exits
        threading.Thread(target=self._event_loop, daemon=True).start()

    def stop(self):
        """Stop the event processing loop."""
        self.running = False
        # Trigger stop condition in _event_loop
        self.queue.put((None, None))

    def _event_loop(self):
        """
        Main event processing loop.

        Continuously processes events from queue and dispatches to subscribers.
        Handles exceptions gracefully to prevent handler failures from breaking bus.
        """
        while self.running:
            # Get next event from queue
            event_type, payload = self.queue.get()

            if event_type is None:
                break

            # Dispatch to handlers subscribed to this event type
            handlers = self.subscribers.get(event_type, [])
            for handler in handlers:
                try:
                    handler(payload)
                except Exception as e:
                    logger.error(f"[EventBus] Handler error for '{event_type}': {e}")
