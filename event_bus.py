# event_bus.py
from collections import defaultdict
from queue import Queue
import threading

class EventBus:
    """The event bus is a single communication stream for all events passed between modules"""
    def __init__(self):
        # The dictionary of subscribers contains a list of topics 
        # Each topic contains a list of subscribers and their handler functions 
        self.subscribers = defaultdict(list)
        # Event bus handlers
        self.queue = Queue()
        self.running = False

    def subscribe(self, event_type, handler):

        self.subscribers[event_type].append(handler)

    def publish(self, event_type, data=None):
        self.queue.put((event_type, data))

    def start(self):
        self.running = True
        # Daemon means that it will automatically die when the main thread stops
        threading.Thread(target=self._event_loop, daemon=True).start()

    def stop(self):
        self.running = False
        # This triggers the stop condition in _event_loops
        self.queue.put((None, None))

    def _event_loop(self):
        while self.running:
            # Get next event from queue
            event_type, payload = self.queue.get()

            if event_type is None:
                break

            # Pass that event to the handlers that are subscribed to the particular event type
            handlers = self.subscribers.get(event_type, [])
            for handler in handlers:
                try:
                    # Pass the payload as an argument to the handler function
                    handler(payload)
                except Exception as e:
                    print(f"[EventBus] Handler error: {e}")