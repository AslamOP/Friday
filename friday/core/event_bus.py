import asyncio, logging
logger = logging.getLogger("friday.event_bus")
class EventBus:
    def __init__(self): self._subscribers: dict[str, list] = {}
    def subscribe(self, event_type: str, callback): self._subscribers.setdefault(event_type, []).append(callback)
    def unsubscribe(self, event_type: str, callback):
        subs = self._subscribers.get(event_type, [])
        if callback in subs:
            subs.remove(callback)
    async def publish(self, event_type: str, data: dict = None):
        for cb in self._subscribers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(cb): await cb(data or {})
                else: cb(data or {})
            except Exception as e: logger.warning("Event callback failed: %s", e)
